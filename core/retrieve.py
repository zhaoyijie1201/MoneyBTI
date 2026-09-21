# -*- coding: utf-8 -*-
"""M2' 人格卡检索 v4：条件即维度。

  每张卡的每条条件 k（指标 x、阈值 t、方向）打成 0–100 分：piecewise(x; 0 → 0, t → 60, 2t → 100)，≤ 型条件取反
  match_c = Σ w_k · score_k / Σ w_k （只算单月可得的条件；requires_history 的条件不计入分母）
  mode=count : 命中 = 达标条件数 ≥ min_required = max(2, round(3 · 可用条件数 / 5))
  mode=any   : 命中 = 任一规则组内全部条件达标；match 取各组加权均值的最大值
  special    : override=true 的卡命中即主人格；override=false 的（月底渡劫人）命中后作为并列人格排第 2
  fallback   : 无命中 → 端水大师（最大类别 < 30%）或最接近的 2 张标「接近但未达到」；data_level 不足 → 数据无法捕获之人
  badges     : 全勤 / 一日暴走 / 薅羊毛 按 trigger_any 判定，只做徽章

v3 原型匹配保留为 retrieve_personas_v3()（用卡上的 signature），v1 阈值检索已移除（v1 trigger 字段不再维护）。
"""
from .kb import PERSONAS, MODIFIER_TAGS, card_for_prompt

HIT_SCORE = 60
CLOSE_MARGIN = 5
DIMS = {d["id"]: d for d in PERSONAS["dimensions"]}
BADGES = PERSONAS.get("badges", [])

_OPS = {">=": lambda a, b: a >= b, "<=": lambda a, b: a <= b, "<": lambda a, b: a < b,
        ">": lambda a, b: a > b, "==": lambda a, b: a == b, "in": lambda a, b: a in b}


# ----------------------------------------------------------------------------- 条件打分
def cond_score(cond, metrics):
    """返回 (score 0–100 | None 不可用, ok, value)。分类型条件（== / in）满足 100 不满足 0。"""
    v = metrics.get(cond["metric"])
    if cond.get("requires_history") or v is None:
        return None, False, v
    op, thr = cond["op"], cond["value"]
    if op in ("==", "in"):
        ok = _OPS[op](v, thr)
        return (100.0 if ok else 0.0), ok, v
    if op in (">=", ">"):
        if thr <= 0:
            s = 100.0 if v > 0 else 0.0
        elif v <= 0:
            s = 0.0
        elif v <= thr:
            s = 60.0 * v / thr
        else:
            s = min(100.0, 60.0 + 40.0 * (v - thr) / thr)
    else:  # <=, <
        if v <= 0:
            s = 100.0
        elif v <= thr:
            s = 100.0 - 40.0 * v / thr if thr > 0 else 100.0
        elif v >= 2 * thr:
            s = 0.0
        else:
            s = 60.0 - 60.0 * (v - thr) / thr
    ok = _OPS[op](v, thr)
    return round(s, 1), ok, v


def _score_group(conds, metrics):
    rows, num, den = [], 0.0, 0.0
    for c in conds:
        s, ok, v = cond_score(c, metrics)
        rows.append({"id": c["id"], "label": c["label"], "label_en": c.get("label_en", c["label"]), "metric": c["metric"], "op": c["op"], "threshold": c["value"],
                     "value": v, "score": s, "ok": ok, "weight": c.get("weight", 1), "available": s is not None,
                     "requires_history": bool(c.get("requires_history"))})
        if s is not None:
            num += c.get("weight", 1) * s; den += c.get("weight", 1)
    return rows, (round(num / den, 1) if den else 0.0)


def card_match(card, metrics):
    """返回 (match, hit, explain)。explain = {mode, conditions | groups, ok_count, min_required, group_index}"""
    if card["mode"] == "count":
        rows, match = _score_group(card["conditions"], metrics)
        avail = [r for r in rows if r["available"]]
        need = max(2, round(3 * len(avail) / 5)) if avail else 99
        okc = sum(1 for r in avail if r["ok"])
        hit = okc >= need and match >= HIT_SCORE        # 校准：达标条数够且整体加权分 ≥ 60，避免 3 条勉强达标、2 条很差也算命中
        return match, hit, {"mode": "count", "conditions": rows, "ok_count": okc, "min_required": need, "available": len(avail)}
    groups, hit, gi, best = [], False, None, -1.0
    for i, conds in enumerate(card["rule_groups"]):
        rows, mt = _score_group(conds, metrics)
        all_ok = all(r["ok"] for r in rows if r["available"]) and any(r["available"] for r in rows)
        rank = mt if i == 0 else round(mt * 0.9, 1)      # 主规则组全额计分，备选规则组 ×0.9（备选是次要信号）
        groups.append({"index": i, "conditions": rows, "match": mt, "rank": rank, "hit": all_ok})
        if (all_ok and not hit) or (all_ok == hit and rank > best):
            hit, best, gi = all_ok or hit, rank, i
    return best, hit, {"mode": "any", "groups": groups, "group_index": gi}


def badges_for(metrics):
    out = []
    for b in BADGES:
        groups = b.get("trigger_any") or [b["trigger"]]
        for conds in groups:
            if all(_OPS[c["op"]](metrics.get(c["metric"]), c["value"]) for c in conds if metrics.get(c["metric"]) is not None) \
                    and all(metrics.get(c["metric"]) is not None for c in conds):
                out.append({"code": b["code"], "name": b["name"], "name_en": b.get("name_en", b["name"]), "emoji": b["emoji"], "line": b.get("line", ""), "line_en": b.get("line_en", b.get("line", "")), "slogan": b.get("slogan", "")})
                break
    return out


def retrieve_personas(metrics, k=3, tier="basic", method="v4"):
    """返回 {candidates:[{code, match, hit, override}], hits, special, close_call, modifier_tags, badges, cards, dimensions, all_matches}。"""
    if method == "v3":
        return retrieve_personas_v3(metrics, k, tier)
    badges = badges_for(metrics)
    if metrics.get("data_level") == "不足":
        return _pack([{"code": "SJWF", "match": 100.0, "hit": True, "override": False}], 0, None, False, [], metrics, {}, [], badges)
    regular, special, explains = [], [], {}
    for card in PERSONAS["cards"]:
        if card["group"] == "fallback":
            continue
        mt, hit, ex = card_match(card, metrics)
        ov = bool(card.get("override")) and hit
        if ov and card.get("override_groups") is not None:      # 只有指定规则组命中才覆盖，其余组并列显示
            ov = any(g["hit"] for g in ex.get("groups", []) if g["index"] in card["override_groups"])
        item = {"code": card["code"], "match": mt, "hit": hit, "override": ov}
        explains[card["code"]] = ex
        (special if card["group"] == "special" else regular).append(item)
    # 按匹配度排序；同分时主规则组命中的卡优先于只靠备选规则组命中的卡
    prim = lambda x: 0 if (explains[x["code"]].get("group_index") in (None, 0)) else 1
    hits = sorted([x for x in regular if x["hit"]], key=lambda x: (-x["match"], prim(x)))
    ranked = hits + sorted([x for x in regular if not x["hit"]], key=lambda x: -x["match"])
    metrics["rule_hits"] = len(hits)
    if not hits and metrics.get("top_category_share", 1) < 0.30:
        cands = [{"code": "DSDS", "match": 100.0, "hit": True, "override": False}]
    else:
        cands = ranked[:k] if hits else ranked[:2]
    close = len(hits) >= 2 and (hits[0]["match"] - hits[1]["match"]) <= CLOSE_MARGIN
    sp_hits = sorted([x for x in special if x["hit"]], key=lambda x: -x["match"])
    sp_code = None
    overrides = [x for x in sp_hits if x["override"]]
    co = [x for x in sp_hits if not x["override"]]
    if overrides:
        sp_code = overrides[0]["code"]
        cands = [overrides[0]] + [c for c in cands if c["code"] != "DSDS"][:2]
    if co:  # 月底渡劫人：并列人格，排第 2
        cands = cands[:1] + [dict(co[0], co_display=True)] + [c for c in cands[1:] if c["code"] != "DSDS"][:1]
        sp_code = sp_code or co[0]["code"]
    tags = [t["tag"] for t in MODIFIER_TAGS
            if (tier == "vip" or not t.get("vip_only")) and all(_tag_ok(c, metrics) for c in t["trigger"])]
    return _pack(cands, len(hits), sp_code, close, tags, metrics, explains, ranked, badges)


def _tag_ok(c, metrics):
    v = metrics.get(c["metric"])
    return v is not None and _OPS[c["op"]](v, c["value"])


def _pack(cands, hits, special, close, tags, metrics, explains, ranked, badges):
    cards = []
    for c in cands:
        card = card_for_prompt(c["code"])
        card.pop("signature", None); card.pop("rules_text", None)
        card.update(match=c["match"], hit=c["hit"], override=c["override"], co_display=c.get("co_display", False),
                    explain=explains.get(c["code"], {}))
        cards.append(card)
    return {"candidates": cands, "hits": hits, "special": special, "close_call": close, "modifier_tags": tags,
            "badges": badges, "cards": cards, "dimensions": metrics.get("dimensions", {}),
            "all_matches": [(r["code"], r["match"]) for r in (ranked or [])]}


# ----------------------------------------------------------------------------- v3 对照（12 维原型匹配）
def dim_sat(score, proto):
    if proto >= 50:
        return max(0.0, 1 - max(0, proto - score) / 50)
    return max(0.0, 1 - max(0, score - proto) / 100)


def card_match_v3(card, metrics):
    sig = card["signature"]; dims = metrics.get("dimensions", {})
    num = den = 0.0
    for d, (proto, w) in sig["dims"].items():
        num += w * dim_sat(dims.get(d, 0), proto); den += w
    match = 100 * num / den if den else 0.0
    for g in sig.get("gates", []):
        actual = metrics.get(g["metric"])
        if actual is None or not _OPS[g["op"]](actual, g["value"]):
            match = min(match, 40)
    return round(match, 1)


def retrieve_personas_v3(metrics, k=3, tier="basic"):
    """v3：12 维原型匹配（只对带 signature 的卡），special / badge 仍按 v4 规则。评估变体 B' 用。"""
    badges = badges_for(metrics)
    if metrics.get("data_level") == "不足":
        return _pack([{"code": "SJWF", "match": 100.0, "hit": True, "override": False}], 0, None, False, [], metrics, {}, [], badges)
    regular, explains = [], {}
    for card in PERSONAS["cards"]:
        if card["group"] == "regular" and card.get("signature"):
            mt = card_match_v3(card, metrics)
            regular.append({"code": card["code"], "match": mt, "hit": mt >= 70, "override": False})
            explains[card["code"]] = {"mode": "v3", "dims": [{"dim": d, "name": DIMS[d]["name"], "emoji": DIMS[d]["emoji"], "score": metrics.get("dimensions", {}).get(d, 0), "proto": p, "weight": w} for d, (p, w) in card["signature"]["dims"].items()]}
    ranked = sorted(regular, key=lambda x: -x["match"])
    hits = [x for x in ranked if x["hit"]]
    metrics["rule_hits"] = len(hits)
    dims = metrics.get("dimensions", {})
    if not hits and (metrics.get("top_category_share", 1) < 0.30 or all(v < 60 for v in dims.values())):
        cands = [{"code": "DSDS", "match": 100.0, "hit": True, "override": False}]
    else:
        cands = ranked[:k] if hits else ranked[:2]
    close = len(hits) >= 2 and (hits[0]["match"] - hits[1]["match"]) <= CLOSE_MARGIN
    sp = []
    for card in PERSONAS["cards"]:
        if card["group"] == "special":
            mt, hit, ex = card_match(card, metrics)
            explains[card["code"]] = ex
            if hit: sp.append({"code": card["code"], "match": mt, "hit": True, "override": bool(card.get("override"))})
    sp_code = None
    ov = [x for x in sp if x["override"]]
    if ov:
        sp_code = ov[0]["code"]; cands = [ov[0]] + [c for c in cands if c["code"] != "DSDS"][:2]
    tags = [t["tag"] for t in MODIFIER_TAGS if (tier == "vip" or not t.get("vip_only")) and all(_tag_ok(c, metrics) for c in t["trigger"])]
    return _pack(cands, len(hits), sp_code, close, tags, metrics, explains, ranked, badges)
