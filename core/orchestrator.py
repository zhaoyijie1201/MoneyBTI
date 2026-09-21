# -*- coding: utf-8 -*-
"""M0 Orchestrator：带决策点与自检的编排器（设计文档第 8 节）。

run_pipeline(path, tier, user_overrides, variant) 走完
  M1 解析 → D0 档位路由 → M2 规则 [→ M3 逐笔 LLM (VIP)] → D1 / D1' / D2 → M4 人工覆盖 → M5 指标
  → M2' 候选检索 → D4 → M6 人格生成 → 代码审查 + M7 LLM 审查 (D3 / D5) → 结果 (M8 渲染由前端做)

返回 dict 里 decisions 记录每个决策点走了哪条分支，llm_calls 记录每次调用的 prompt / 原始输出（调试抽屉）。
"""
import re
from collections import Counter

from . import prompts as P
from .kb import CATEGORIES, DEFAULTS, CARDS, RULES, card_for_prompt
from .parser import parse_bill, to_llm_row, raw_rows
from .classify import apply_basic, apply_user_labels, tag_flags
from .metrics import compute_metrics
from .retrieve import retrieve_personas, DIMS
from .llm import call_json, chat, LLMError

M3_BATCH = 40
FORBIDDEN_WORDS = ["上瘾", "焦虑", "危险", "抠门", "月光族", "败家", "剁手", "成瘾", "沉迷",
                   "addict", "anxiety", "dangerous", "stingy", "cheapskate", "shopaholic", "broke", "reckless", "wasteful"]
FORBIDDEN_WORDS_STRICT = ["病", "穷"]           # 单字，只在非人格名文本里查
VIP_ONLY_WORDS = ["冲动", "餐次", "夜宵", "加班", "宅家", "周末出游", "通勤时段", "场景", "impulse", "meal slot", "late-night snack", "overtime", "staying in", "weekend outing"]
CLOSE_WORDS = ["势均力敌", "只差一点", "不相上下", "难分高下", "并列", "平分秋色", "差一点", "接近", "neck and neck", "close call", "close second", "almost a tie", "nearly tied", "too close"]
ADVICE_WORDS = ["建议", "应该", "少花", "节省", "存钱", "理财", "预算", "控制一下", "戒掉", "you should", "cut back", "save money", "budget", "invest", "quit"]
RATIO_KEYS = {"txn_per_day": False}


# ----------------------------------------------------------------------------- 指标 → prompt 视图
def _pct(v):
    return f"{v * 100:.1f}%"


PROMPT_CAT = dict(CATEGORIES, C10="学习/其他(含未归类)")
PROMPT_CAT_EN = dict(RULES["_meta"].get("categories_en", {}), C10="Learning / other (incl. uncategorised)")


def metrics_for_prompt(m, tier, lang="zh"):
    CAT = PROMPT_CAT_EN if lang == "en" else PROMPT_CAT
    """把比例转成 '47.7%' 字符串，类别带中文名，去掉 hour_hist / highlights_candidates 等大字段。"""
    ratio_keys = ["top_category_share", "food_share", "delivery_ratio", "small_txn_ratio", "big_ticket_share",
                  "online_share", "shopping_share", "late_night_ratio", "commute_count_ratio", "necessity_share",
                  "weekend_share", "front_loading", "C2_share", "C3_share", "C4_share", "C6_share", "C8_share",
                  "C9_share", "C10_share", "game_share", "travel_share", "active_days_ratio", "max_day_share",
                  "discount_txn_ratio", "top_merchant_count_share", "unclassified_ratio"]
    plain_keys = ["total", "txn_count", "txn_per_day", "active_days", "period_days", "period_start", "period_end",
                  "data_level", "median_amount", "beverage_per_week", "distinct_C2_merchants", "subscription_brands",
                  "max_day", "max_day_txn_count", "transfer_count", "top_merchants", "outliers", "unclassified_amount"]
    out = {k: m[k] for k in plain_keys if k in m}
    out["dimensions"] = {f"{DIMS[d]['emoji']} {DIMS[d].get('name_en', DIMS[d]['name']) if lang == 'en' else DIMS[d]['name']}": v for d, v in m.get("dimensions", {}).items()}
    unc = "uncategorised" if lang == "en" else "未分类"
    out["top_category"] = f"{m['top_category']} {CAT.get(m['top_category'], '')}".strip() if m.get("top_category") else None
    out["category_share"] = {f"{c} {CAT.get(c, c)}": _pct(v) for c, v in m["category_share"].items()}
    out["category_amount"] = {f"{c} {CAT.get(c, unc)}": v for c, v in m["category_amount"].items()}
    out["category_count"] = {f"{c} {CAT.get(c, unc)}": v for c, v in m["category_count"].items()}
    if m.get("ambiguous_rows"):
        out["ambiguous_rows_pending_user_confirmation"] = m["ambiguous_rows"]
        out["ambiguous_amount_share"] = _pct(m.get("ambiguous_amount_share", 0))
    for k in ratio_keys:
        if k in m:
            out[k] = _pct(m[k])
    if tier == "vip":
        for k in ("impulse_share", "after_work_share", "late_meal_ratio"):
            if k in m:
                out[k] = _pct(m[k])
        for k in ("meal_slot_dist", "scene_dist"):
            if k in m:
                out[k] = {kk: _pct(vv) for kk, vv in m[k].items()}
    return out


# ----------------------------------------------------------------------------- 代码级审查（M7 的确定性部分）
_NUM = re.compile(r"(\d+(?:,\d{3})*(?:\.\d+)?)\s*(%|％)?")
_SKIP_AFTER = re.compile(r"^\s*(点|时|日|号|月|分|秒|楼|段|星期|周|年|次方)")


def _allowed_numbers(m, highlights):
    pcts, nums = set(), set()
    for k, v in m.items():
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            if 0 <= v <= 1 and k not in ("total", "median_amount", "txn_per_day", "beverage_per_week", "period_days",
                                         "txn_count", "active_days", "distinct_C2_merchants", "subscription_brands",
                                         "max_day_txn_count", "transfer_count", "unclassified_amount"):
                pcts.add(v * 100)
            nums.add(float(v))
    for d in (m.get("category_share", {}), m.get("meal_slot_dist", {}), m.get("scene_dist", {})):
        pcts.update(v * 100 for v in d.values())
    nums.update(float(v) for v in m.get("category_amount", {}).values())
    nums.update(float(v) for v in m.get("category_count", {}).values())
    nums.update(float(c) for _, c in m.get("top_merchants", []))
    nums.update(float(o["amount"]) for o in m.get("outliers", []))
    nums.update(float(h["amount"]) for h in highlights)
    nums.update(float(v) for v in m.get("dimensions", {}).values())          # 维度分
    nums.update((20.0, 200.0, 60.0))                                          # 指标定义常量：小额 ≤20、大额 ≥200、维度 60 分（F13）
    for k, v in m.items():                                                     # v4 条件指标（笔数 / 周数 / 次数）
        if isinstance(v, (int, float)) and not isinstance(v, bool) and k.endswith(("_cnt", "_cnt_or_top3", "_days", "_streak", "_repeat", "_categories", "_modes", "_merchants", "_slots", "_le350")):
            nums.add(float(v))
    nums.update(float(r["amount"]) for r in m.get("ambiguous_rows", []))
    return pcts, nums


def check_numbers(text, pcts, nums, tol_pp=3.0):
    """文案里的数字必须出现在指标里：百分比允许 ±3 pp（E2 标准），其他数字允许 ±1%。返回违规数字列表。"""
    bad = []
    for mt in _NUM.finditer(text):
        raw, pct = mt.group(1), mt.group(2)
        if not pct and _SKIP_AFTER.match(text[mt.end():]):
            continue
        x = float(raw.replace(",", ""))
        if pct:
            if not any(abs(x - p) <= tol_pp for p in pcts):
                bad.append(raw + "%")
        else:
            if not any(abs(x - n) <= max(0.01 * n, 0.5) for n in nums) and not any(abs(x - p) <= tol_pp for p in pcts):
                bad.append(raw)
    return bad


def code_check(out, ctx):
    """返回违规列表（空 = 通过）。ctx: tier, candidate_codes, override_code, metrics, highlights, do_not_say, data_level。"""
    v = []
    codes = ctx["candidate_codes"]
    if out.get("primary_persona") not in codes:
        v.append(f"primary_persona {out.get('primary_persona')} 不在候选 {codes} 内")
    if ctx.get("override_code") and out.get("primary_persona") != ctx["override_code"]:
        v.append(f"候选首位 {ctx['override_code']} 是 override 成就卡，必须作为 primary_persona")
    sec = out.get("secondary_persona")
    if sec and sec not in codes:
        v.append(f"secondary_persona {sec} 不在候选内")
    if sec and sec == out.get("primary_persona"):
        v.append("secondary_persona 不能与 primary_persona 相同")
    for c in ctx.get("not_hit_codes", []):
        if out.get("primary_persona") == c and not ctx.get("allow_not_hit"):
            v.append(f"{c} 是「接近但未达到」的卡，不能作为 primary_persona")
    texts = [out.get("summary", ""), out.get("one_liner", ""), out.get("keyword", "")]
    texts += [e.get("text", "") + " " + str(e.get("value", "")) for e in out.get("evidence", []) or []]
    texts += [h.get("text", "") for h in out.get("highlights", []) or []]
    joined = " ".join(texts)
    if ctx.get("lang") == "en":
        if len(out.get("summary", "")) > 220:
            v.append(f"summary is too long ({len(out['summary'])} characters, limit 220) - rewrite it shorter, still in English")
        if len(out.get("one_liner", "")) > 80:
            v.append(f"one_liner is too long ({len(out['one_liner'])} characters, limit 80) - rewrite it shorter, still in English")
        cjk = re.compile(r"[\u4e00-\u9fff]")
        texts = [out.get("summary", ""), out.get("one_liner", ""), out.get("keyword", "")] + [e.get("text", "") for e in out.get("evidence", [])] + [h.get("text", "") for h in out.get("highlights", [])]
        if any(cjk.search(str(t)) for t in texts):
            v.append("language: summary / one_liner / keyword / evidence.text / highlights.text must be written in English - no Chinese characters")
    else:
        if len(out.get("summary", "")) > 60:
            v.append(f"summary 超过 60 字（{len(out['summary'])}）")
        if len(out.get("one_liner", "")) > 25:
            v.append(f"one_liner 超过 25 字（{len(out['one_liner'])}）")
    if not out.get("evidence"):
        v.append("evidence 为空，至少引用一个指标")
    pcts, nums = _allowed_numbers(ctx["metrics"], ctx["highlights"])
    for mt in ctx.get("matches", []):                                           # 匹配度既可写 87% 也可写 87 分
        pcts.add(mt); nums.add(mt)
    bad = check_numbers(joined, pcts, nums)
    if bad:
        v.append(f"这些数字不在指标里（不得自行计算）: {bad}")
    if ctx["tier"] == "basic":
        if sec:
            v.append("basic 档 secondary_persona 必须为 null")
        if out.get("modifier_tags"):
            v.append("basic 档 modifier_tags 必须为空")
        if out.get("highlights"):
            v.append("basic 档 highlights 必须为空")
        hit = [w for w in VIP_ONLY_WORDS if w in joined]
        if hit:
            v.append(f"basic 档不得提及 VIP 字段: {hit}")
    else:
        hl_keys = {(h["date"], round(float(h["amount"]), 2)) for h in ctx["highlights"]}
        for h in out.get("highlights", []) or []:
            try:
                k = (str(h.get("date")), round(float(h.get("amount")), 2))
            except (TypeError, ValueError):
                k = None
            if k not in hl_keys:
                v.append(f"highlight {h} 不在 highlights_candidates 内")
        if len(out.get("highlights", []) or []) > 3:
            v.append("highlights 最多 3 条")
        for t in out.get("modifier_tags", []) or []:
            if t not in ctx.get("modifier_tags", []):
                v.append(f"modifier_tag {t} 不是检索给出的标签")
    fw = [w for w in FORBIDDEN_WORDS if w in joined] + [w for w in FORBIDDEN_WORDS_STRICT if w in joined]
    if fw:
        v.append(f"含禁词 {fw}")
    aw = [w for w in ADVICE_WORDS if w in joined]
    if aw:
        v.append(f"疑似理财建议用语 {aw}")
    chosen = {out.get("primary_persona"), out.get("secondary_persona")} - {None}
    key = "do_not_say_en" if ctx.get("lang") == "en" else "do_not_say"
    dns_scope = [p for code in chosen for p in (CARDS.get(code, {}).get(key) or CARDS.get(code, {}).get("do_not_say", []))]   # 只查被选中人格的禁语（F15）
    dns = sorted({p for p in dns_scope if p and p in joined})
    if dns:
        v.append(f"含所选人格卡 do_not_say 禁语 {dns}")
    if ctx.get("close_call"):
        if out.get("confidence") == "high":
            v.append("两张候选卡强度接近（差 ≤ 0.1），confidence 不能是 high")
        if not any(w in out.get("summary", "") for w in CLOSE_WORDS):
            v.append(f"两张候选卡势均力敌，summary 必须点明（用 {CLOSE_WORDS[0]} / {CLOSE_WORDS[1]} 之类的话）")
    if ctx.get("ambiguous_share", 0) >= 0.30 and not any(w in joined for w in ("待确认", "未确认", "确认", "pending confirmation", "unconfirmed", "to be confirmed")):
        v.append("有占总额 ≥ 30% 的 R8 待确认交易（房租 / 押金 / 收款码），summary 必须写明这笔钱待确认，不得据此下结论")
    if ctx.get("data_level") == "勉强" and not any(w in out.get("summary", "") for w in ("仅供一乐", "just for fun", "small sample")):
        v.append("data_level=勉强 时 summary 必须含「样本有点少，仅供一乐」")
    return v


# ----------------------------------------------------------------------------- M3 逐笔分析（VIP）
VALID_CATS = set(CATEGORIES)


def _apply_m3_row(t, r):
    c = r.get("category")
    if c not in VALID_CATS:
        return False
    try:
        conf = float(r.get("confidence", 0.5))
    except (TypeError, ValueError):
        conf = 0.5
    if conf <= 0.3:                     # F11：说明为空 / 商户脱敏时不硬判，留未分类给 M4 / D1'
        t["category"] = None
        t["confidence"] = conf
        t["source_of_label"] = None
        t["vip"] = {"brand": r.get("brand") or t["merchant"], "meal_slot": "非餐饮", "scene": "未知", "impulse": 0.0,
                    "reason": r.get("reason", ""), "suggested_category": c}
        return True
    t["category"] = c
    t["is_online"] = bool(r.get("is_online", DEFAULTS[c]["is_online"]))
    t["is_necessity"] = bool(r.get("is_necessity", DEFAULTS[c]["is_necessity"]))
    try:
        t["confidence"] = max(0.0, min(1.0, float(r.get("confidence", 0.5))))
    except (TypeError, ValueError):
        t["confidence"] = 0.5
    t["source_of_label"] = "llm"
    try:
        imp = float(r.get("impulse", 0.3))
    except (TypeError, ValueError):
        imp = 0.3
    t["vip"] = {"brand": r.get("brand") or t["merchant"], "meal_slot": r.get("meal_slot") or "非餐饮",
                "scene": r.get("scene") or "未知", "impulse": max(0.0, min(1.0, imp)), "reason": r.get("reason", "")}
    if c == "C8" and (t["rule_id"] == "M15" or t["platform_category"] == "酒店旅游"):
        t["brand_family"] = "travel"
    tag_flags(t)
    return True


def run_m3(txns, log, second_pass=False, salt=""):
    """按批调用 M3；返回 (成功行数, 失败行数)。失败的行保留规则结果。"""
    ok = fail = 0
    for i in range(0, len(txns), M3_BATCH):
        batch = txns[i:i + M3_BATCH]
        rows = [to_llm_row(t) for t in batch]
        user = (P.M3_USER_SECOND_PASS if second_pass else P.M3_USER).format(batch_json=P.dumps(rows))
        try:
            obj, meta = call_json(P.M3_SYSTEM, user, temperature=0.1, max_tokens=6000, salt=salt, module="M3")
        except LLMError as e:
            log.append({"module": "M3", "error": str(e), "batch": i // M3_BATCH}); fail += len(batch); continue
        results = obj.get("results") if isinstance(obj, dict) else obj
        by_id = {r.get("id"): r for r in (results or []) if isinstance(r, dict)}
        log.append({"module": "M3" + ("-2nd" if second_pass else ""), "system": P.M3_SYSTEM, "user": user, "raw": meta["text"],
                    "cached": meta["cached"], "prompt_tokens": meta["prompt_tokens"], "completion_tokens": meta["completion_tokens"],
                    "latency": meta["latency"], "model": meta.get("model")})
        for t in batch:
            r = by_id.get(t["id"])
            if r and _apply_m3_row(t, r):
                ok += 1
            else:
                fail += 1
    return ok, fail


# ----------------------------------------------------------------------------- 兜底文案
def fallback_persona(code, metrics, tier, reason, lang="zh"):
    card = CARDS[code]
    en = lang == "en"
    ev = []
    conds = card.get("conditions") or (card.get("rule_groups") or [[]])[0]
    for c in conds:
        val = metrics.get(c["metric"])
        if val is not None and not c.get("requires_history"):
            shown = _pct(val) if isinstance(val, float) and 0 <= val <= 1 and "amount" not in c["metric"] else val
            ev.append({"metric": c["metric"], "value": shown, "text": f"{c.get('label_en', c['label']) if en else c['label']}: {shown}"})
    tag = (card.get("tagline_en") or card["tagline"]) if en else card["tagline"]
    return {"primary_persona": code, "secondary_persona": None, "rarity": card["rarity"], "confidence": "low",
            "evidence": ev[:3], "summary": tag, "one_liner": tag, "keyword": (card.get("name_en") or card["name"]) if en else card["name"],
            "modifier_tags": [], "highlights": [], "fallback": True, "fallback_reason": reason}


def fallback_copy(code, lang="zh"):
    card = CARDS[code]
    return {"pass": True, "violations": [], "slogan": (card.get("slogan_examples") or ["SPEND HAPPILY."])[0],
            "mood_emojis": [card["emoji"], "💸", "🧾", "✨"], "thank_you_line": "Thanks, see you next month" if lang == "en" else "谢谢惠顾，下月再见", "fallback": True}


# ----------------------------------------------------------------------------- 主流程
def stage_classify(path, tier="basic", use_llm=True, salt=""):
    """M1 → D0 → M2 [→ M3 → D2]。返回 dict(txns(含 dt), report, layers, m3, decisions, log)。"""
    decisions, log = [], []
    txns, report = parse_bill(path)
    decisions.append({"point": "D0", "branch": tier, "note": "普通 → 三层规则；VIP → 规则预标注 + M3 逐笔"})
    layers = apply_basic(txns)
    m3_stats = None
    if tier == "vip" and use_llm and txns:
        ok, fail = run_m3(txns, log, salt=salt)
        m3_stats = {"llm_rows": ok, "rule_fallback_rows": fail}
        low = [t for t in txns if t.get("confidence", 1) < 0.5]
        if txns and len(low) / len(txns) >= 0.10:
            run_m3(low, log, second_pass=True, salt=salt)
            still = [t["id"] for t in txns if t.get("confidence", 1) < 0.5]
            decisions.append({"point": "D2", "branch": "second_pass", "low_before": len(low), "low_after": len(still)})
            m3_stats["low_confidence_ids"] = still
        else:
            decisions.append({"point": "D2", "branch": "skip", "low": len(low)})
            m3_stats["low_confidence_ids"] = [t["id"] for t in low]
    return {"txns": txns, "report": report, "layers": layers, "m3": m3_stats, "decisions": decisions, "log": log}


def stage_metrics(txns, report, tier="basic", user_overrides=None, method="v4", decisions=None):
    """M4 → M5 → D1 / D1' → M2' → D4。返回 dict(metrics, retrieval, warnings, decisions)。"""
    decisions = decisions if decisions is not None else []
    if user_overrides:
        apply_user_labels(txns, user_overrides)
        decisions.append({"point": "M4", "branch": "user_overrides", "count": len(user_overrides)})
    metrics = compute_metrics(txns, report=report)
    decisions.append({"point": "D1", "branch": metrics["data_level"]})
    warnings = []
    if tier == "basic" and metrics["unclassified_ratio"] >= 0.40:
        n_unc = metrics["category_count"].get("UNC", 0)
        warnings.append(f"规则只认出 {1 - metrics['unclassified_ratio']:.0%} 的交易，{n_unc} 笔未分类：可切换 VIP 或在分类表里手动补全")
        decisions.append({"point": "D1'", "branch": "warn", "unclassified_ratio": metrics["unclassified_ratio"]})
    retrieval = retrieve_personas(metrics, tier=tier, method=method)
    cands = retrieval["candidates"]
    decisions.append({"point": "D4", "branch": "single" if len(cands) == 1 else "multiple", "candidates": [c["code"] for c in cands],
                      "close_call": retrieval.get("close_call")})
    return {"metrics": metrics, "retrieval": retrieval, "warnings": warnings, "decisions": decisions}


def stage_generate(tier, metrics, retrieval, use_llm=True, salt="", decisions=None, log=None, lang="zh"):
    """D1 不足 → 神秘人；否则 M6 → 代码审查 + M7（D3 / D5）。返回 dict(persona, copy, review, decisions, log)。"""
    decisions = decisions if decisions is not None else []
    log = log if log is not None else []
    cands = retrieval["candidates"]
    if metrics["data_level"] == "不足":
        missing = []
        en_ = lang == "en"
        if metrics["txn_count"] < 10: missing.append(f"only {metrics['txn_count']} valid transactions (need ≥ 10)" if en_ else f"有效交易只有 {metrics['txn_count']} 笔（需要 ≥ 10）")
        if metrics["active_days"] <= 1: missing.append("all spending on a single day" if en_ else "消费集中在 1 天")
        if len([c for c in metrics["category_count"] if c != "UNC"]) <= 1: missing.append("only one spending category" if en_ else "只有 1 个消费类别")
        if metrics["unclassified_ratio"] >= 0.4: missing.append("most rows unrecognised by rules - label them manually or switch to VIP" if en_ else "大部分交易规则认不出，请手动分类或切换 VIP")
        p = fallback_persona("SJWF", metrics, tier, "data_level=不足", lang)
        p["summary"] = ("Too thin to read you: " if lang == "en" else "账单太薄，看不透你：") + ("; " if lang == "en" else "；").join(missing)
        p["confidence"] = "low"
        decisions.append({"point": "D1", "branch": "SMR", "missing": missing})
        return {"persona": p, "copy": fallback_copy("SJWF", lang), "review": {"pass": True, "violations": [], "attempts": 0},
                "decisions": decisions, "log": log}
    if not use_llm:
        return {"persona": fallback_persona(cands[0]["code"], metrics, tier, "use_llm=False", lang), "copy": fallback_copy(cands[0]["code"], lang),
                "review": {"pass": True, "violations": [], "attempts": 0}, "decisions": decisions, "log": log}
    persona, review = run_m6_m7(tier, metrics, retrieval, log, decisions, salt=salt, lang=lang)
    return {"persona": persona, "copy": review.get("copy"), "review": {k: v for k, v in review.items() if k != "copy"},
            "decisions": decisions, "log": log}


def run_pipeline(path, tier="basic", user_overrides=None, variant=None, use_llm=True, salt="", method="v4", lang="zh"):
    """variant: None (按 tier) | "A" 最小 LLM。salt 区分同一账单的多轮运行（绕过缓存）。method: v4 条件即维度 | v3 十二维原型匹配（评估对照）。
    三段式：stage_classify → stage_metrics → stage_generate（API 分别暴露为三个接口）。返回 dict（txns 已去掉 dt 对象）。"""
    if variant == "A":
        return run_variant_a(path, [], salt)
    c = stage_classify(path, tier, use_llm, salt)
    m = stage_metrics(c["txns"], c["report"], tier, user_overrides, method, c["decisions"])
    g = stage_generate(tier, m["metrics"], m["retrieval"], use_llm, salt, c["decisions"], c["log"], lang=lang)
    return {"tier": tier, "method": method, "salt": salt, "report": c["report"], "layers": c["layers"], "m3": c["m3"],
            "metrics": m["metrics"], "retrieval": m["retrieval"], "warnings": m["warnings"], "decisions": c["decisions"],
            "llm_calls": c["log"], "txns": [{k: v for k, v in t.items() if k != "dt"} for t in c["txns"]],
            "persona": g["persona"], "copy": g["copy"], "review": g["review"]}


def run_m6_m7(tier, metrics, retrieval, log, decisions, max_attempts=2, salt="", lang="zh"):
    en = lang == "en"
    cands = retrieval["candidates"]
    codes = [c["code"] for c in cands]
    override = cands[0]["code"] if cands[0].get("override") else None
    ctx = {"tier": tier, "candidate_codes": codes, "override_code": override,
           "not_hit_codes": [c["code"] for c in cands if not c["hit"]],
           "allow_not_hit": not any(c["hit"] for c in cands),          # 全部未命中时允许选最接近的卡
           "metrics": metrics, "highlights": metrics.get("highlights_candidates", []),
           "modifier_tags": retrieval["modifier_tags"], "data_level": metrics["data_level"],
           "do_not_say": [p for card in retrieval["cards"] for p in (card.get("do_not_say_en" if lang == "en" else "do_not_say") or card.get("do_not_say", []))]}
    ctx["close_call"] = bool(retrieval.get("close_call")); ctx["lang"] = lang
    ctx["ambiguous_share"] = metrics.get("ambiguous_amount_share", 0)
    ctx["matches"] = [float(c["match"]) for c in cands]
    mp = metrics_for_prompt(metrics, tier, lang)
    hl = ctx["highlights"] if tier == "vip" else []
    cards_json = []
    for card in retrieval["cards"]:
        drop = {"explain", "signature", "conditions", "rule_groups", "guardrails", "distinguish", "core_categories", "rules_text",
                "illustration_prompt", "focus", "guardrails_en", "distinguish_en", "core_categories_en", "focus_en"}
        c = {k: v for k, v in card.items() if k not in drop and not (k.endswith("_en") if not en else k in ("name", "tagline", "interpretation", "traits", "tone", "do_not_say", "axis", "summary_examples", "slogan_examples_cn"))}
        if en:   # 英文：用 *_en 字段顶替中文字段名，模型只看到一套
            for k in ("name", "tagline", "interpretation", "traits", "tone", "do_not_say", "axis"):
                if card.get(k + "_en"): c[k] = card[k + "_en"]
                c.pop(k + "_en", None)
            c["summary_examples"] = [x for x in (c.get("tagline"), (c.get("interpretation") or "")[:120]) if x]
        ex = card.get("explain") or {}
        rows = ex.get("conditions") or [r for g in ex.get("groups", []) for r in g["conditions"]]
        c["fit"] = [{"condition": (r.get("label_en") if en else r["label"]) or r["label"], "value": r["value"], "threshold": r["threshold"], "score": r["score"], "ok": r["ok"]}
                    for r in rows if r.get("available")]
        if ex.get("mode") == "count":
            c["fit_summary"] = f"{ex['ok_count']} / {ex['available']} 条件达标（需 ≥ {ex['min_required']}）"
        cards_json.append(c)
    badges_json = retrieval.get("badges", [])
    feedback, violations, last_out, copy_out = "", [], None, None
    for attempt in range(1, max_attempts + 1):
        mp["badges"] = [f"{b['emoji']} {b.get('name_en', b['name']) if en else b['name']}: {b.get('line_en', b['line']) if en else b['line']}" for b in badges_json]
        system6 = P.M6_SYSTEM.replace("{lang_rule}", P.M6_LANG["en" if en else "zh"])
        user = P.M6_USER.format(tier=tier, lang=lang, close_call=P.dumps(ctx["close_call"]), metrics_json=P.dumps(mp), candidates_json=P.dumps(cards_json),
                                tags_json=P.dumps(retrieval["modifier_tags"] if tier == "vip" else []),
                                highlights_json=P.dumps(hl), feedback=feedback)
        try:
            out, meta = call_json(system6, user, temperature=0.3, max_tokens=2000, salt=f"{salt}attempt{attempt}", module="M6")
        except LLMError as e:
            log.append({"module": "M6", "error": str(e), "attempt": attempt})
            decisions.append({"point": "D3", "branch": "invalid_json", "attempt": attempt})
            violations = [str(e)]; continue
        log.append({"module": "M6", "attempt": attempt, "system": system6, "user": user, "raw": meta["text"], "cached": meta["cached"],
                    "prompt_tokens": meta["prompt_tokens"], "completion_tokens": meta["completion_tokens"], "latency": meta["latency"], "model": meta.get("model")})
        out.setdefault("secondary_persona", None); out.setdefault("modifier_tags", []); out.setdefault("highlights", [])
        if tier == "basic" and (out.get("secondary_persona") or out.get("modifier_tags") or out.get("highlights")):
            decisions.append({"point": "D3", "branch": "normalise_basic", "attempt": attempt,
                              "dropped": {"secondary_persona": out.get("secondary_persona"), "modifier_tags": out.get("modifier_tags"),
                                          "highlights": len(out.get("highlights") or [])}})
            out["secondary_persona"] = None; out["modifier_tags"] = []; out["highlights"] = []      # F12：档位字段由代码归一化
        out.setdefault("evidence", []); out.setdefault("rarity", CARDS.get(out.get("primary_persona"), {}).get("rarity"))
        last_out = out
        violations = code_check(out, ctx)
        decisions.append({"point": "D3", "branch": "code_check", "attempt": attempt, "violations": violations})
        # M7：文案 + LLM 审查（语气、禁语、建议）
        system7 = P.M7_SYSTEM.replace("{thank_lang}", P.M7_THANK["en" if en else "zh"])
        user7 = P.M7_USER.format(tier=tier, lang=lang, close_call=P.dumps(ctx["close_call"]), persona_json=P.dumps(out), codes_json=P.dumps(codes), dns_json=P.dumps(ctx["do_not_say"]),
                                 metrics_json=P.dumps({k: mp[k] for k in ("total", "txn_count", "top_category", "category_share", "data_level") if k in mp}),
                                 highlights_json=P.dumps(hl), code_check=P.dumps(violations))
        try:
            rev, meta7 = call_json(system7, user7, temperature=0.3, max_tokens=800, salt=f"{salt}attempt{attempt}", module="M7")
            log.append({"module": "M7", "attempt": attempt, "system": system7, "user": user7, "raw": meta7["text"], "cached": meta7["cached"],
                        "prompt_tokens": meta7["prompt_tokens"], "completion_tokens": meta7["completion_tokens"], "latency": meta7["latency"], "model": meta7.get("model")})
        except LLMError as e:
            log.append({"module": "M7", "error": str(e), "attempt": attempt})
            rev = {"pass": not violations, "violations": [], "_error": str(e)}
        copy_out = rev
        llm_v = list(rev.get("violations") or []) if not rev.get("pass", False) else []
        all_v = violations + llm_v
        decisions.append({"point": "D5", "branch": "pass" if not all_v else "fail", "attempt": attempt, "llm_violations": llm_v})
        if not all_v:
            return out, {"pass": True, "violations": [], "attempts": attempt, "copy": _copy_fields(rev, out["primary_persona"], lang)}
        feedback = P.M6_FEEDBACK.format(violations="\n".join(f"- {x}" for x in all_v)) + ("\nKeep every text field in English." if en else "")
        violations = all_v
    # 两次都失败 → 默认文案兜底
    code = override or codes[0]
    decisions.append({"point": "D5", "branch": "fallback", "violations": violations})
    p = fallback_persona(code, metrics, tier, "AI 文案未通过审查，已使用默认文案", lang)
    if last_out and last_out.get("primary_persona") in codes and not (override and last_out["primary_persona"] != override):
        p["primary_persona"] = last_out["primary_persona"]; p["rarity"] = CARDS[p["primary_persona"]]["rarity"]
    cp = _copy_fields(copy_out or {}, p["primary_persona"], lang) if copy_out and copy_out.get("slogan") else fallback_copy(p["primary_persona"], lang)
    return p, {"pass": False, "violations": violations, "attempts": max_attempts, "copy": cp, "fallback": True}


def _copy_fields(rev, code, lang="zh"):
    fb = fallback_copy(code, lang)
    emojis = rev.get("mood_emojis") or fb["mood_emojis"]
    if not isinstance(emojis, list) or len(emojis) != 4:
        emojis = (list(emojis) + fb["mood_emojis"])[:4] if isinstance(emojis, list) else fb["mood_emojis"]
    return {"slogan": (rev.get("slogan") or fb["slogan"])[:40], "mood_emojis": emojis,
            "thank_you_line": (rev.get("thank_you_line") or fb["thank_you_line"])[:40 if lang == "en" else 15]}


# ----------------------------------------------------------------------------- 变体 A
def run_variant_a(path, log, salt=""):
    """变体 A：不清洗、不算指标、不给人格体系，脱敏原始行 + 一句话 prompt。"""
    rows = raw_rows(path)
    user = P.A_USER.format(rows_text="\n".join(rows))
    try:
        out, meta = call_json(P.A_SYSTEM, user, temperature=0.3, max_tokens=800, salt=salt, module="M6")
        log.append({"module": "A", "system": P.A_SYSTEM, "user": user, "raw": meta["text"], "cached": meta["cached"],
                    "prompt_tokens": meta["prompt_tokens"], "completion_tokens": meta["completion_tokens"], "latency": meta["latency"]})
    except LLMError as e:
        out = {"persona_name": None, "summary": "", "one_liner": "", "error": str(e)}
        log.append({"module": "A", "error": str(e)})
    return {"tier": "A", "salt": salt, "report": {"raw": len(rows)},
            "persona": {"primary_persona": None, "persona_name": out.get("persona_name"),
                        "summary": out.get("summary", ""), "one_liner": out.get("one_liner", ""), "evidence": []},
            "copy": None, "review": None, "decisions": [], "llm_calls": log, "txns": []}


def llm_usage(result):
    calls = [c for c in result.get("llm_calls", []) if "error" not in c]
    return {"calls": len(calls), "cached": sum(c.get("cached", False) for c in calls),
            "prompt_tokens": sum(c.get("prompt_tokens", 0) for c in calls),
            "completion_tokens": sum(c.get("completion_tokens", 0) for c in calls),
            "by_module": dict(Counter(c["module"] for c in calls))}
