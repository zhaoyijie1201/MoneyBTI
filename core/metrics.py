# -*- coding: utf-8 -*-
"""M5 Metrics：K1–K33 指标（代码计算，不经 LLM）。
相对 rag/retrieval.py 首版的修正：
  * data_level 按 3.5 节三条件：充足 = 笔数 ≥ 30 且 天数 ≥ 10 且 类别 ≥ 3
  * front_loading 用账单起始日（period_start），不用首笔交易日
  * 新增 top_merchants、highlights_candidates、VIP 指标 K16–K18（若交易带 vip 字段）
"""
import statistics
from collections import Counter, defaultdict
from datetime import date

from .kb import PERSONAS, RULES

_FAM = {f["id"]: f for f in RULES["L1_merchant_families"]}
_MK = RULES.get("metric_keywords", {})


def _pct(a, b, nd=3):
    return round(a / b, nd) if b else 0.0


def compute_metrics(txns, report=None):
    report = report or {}
    days = sorted({t["dt"].date() for t in txns})
    period_start = date.fromisoformat(report["period_start"]) if report.get("period_start") else (days[0] if days else None)
    period_days = report.get("period_days") or (max(1, (days[-1] - days[0]).days + 1) if days else 1)
    n = len(txns)
    total = sum(t["amount"] for t in txns)
    cat_amt, cat_cnt = defaultdict(float), Counter()
    day_amt, day_cnt, merchant_cnt = defaultdict(float), Counter(), Counter()
    travel_amt, game_amt, after_work = 0.0, 0.0, 0.0
    sub_brands, c2_merchants = set(), set()
    for t in txns:
        c = t.get("category") or "UNC"
        cat_amt[c] += t["amount"]; cat_cnt[c] += 1
        d = t["dt"].date()
        day_amt[d] += t["amount"]; day_cnt[d] += 1
        merchant_cnt[t["merchant"]] += 1
        rid = t.get("rule_id") or ""
        is_travel = rid == "M15" or t["platform_category"] == "酒店旅游" or t.get("brand_family") == "travel"
        if c == "C8":
            if is_travel:
                travel_amt += t["amount"]
            else:
                game_amt += t["amount"]
        if rid == "M14" or any(k in t["description"] for k in ("会员", "订阅", "连续包月")):
            sub_brands.add(t["merchant"])
        if c == "C2":
            c2_merchants.add(t["merchant"])
        if t["weekday"] < 5 and 17 <= t["hour"] < 21:
            after_work += t["amount"]
    classified_total = sum(v for c, v in cat_amt.items() if c != "UNC")
    cshare = {c: cat_amt[c] / classified_total for c in cat_amt if c != "UNC"} if classified_total else {}
    top = max(cshare, key=cshare.get) if cshare else None
    amts = sorted(t["amount"] for t in txns)
    food = sum(cshare.get(c, 0) for c in ("C1", "C2", "C4"))
    dsum = cat_amt["C1"] + cat_amt["C2"] + cat_amt["C3"]
    weeks = max(1, period_days / 7)
    max_day = max(day_amt, key=day_amt.get) if day_amt else None

    m = {
        # K1–K4
        "total": round(total, 2), "txn_count": n, "txn_per_day": round(n / period_days, 2),
        "active_days": len(days), "period_days": period_days,
        "period_start": report.get("period_start"), "period_end": report.get("period_end"),
        "category_share": {c: round(v, 3) for c, v in sorted(cshare.items(), key=lambda x: -x[1])},
        "category_amount": {c: round(v, 2) for c, v in sorted(cat_amt.items(), key=lambda x: -x[1])},
        "category_count": dict(cat_cnt),
        "unclassified_ratio": _pct(cat_cnt["UNC"], n),
        "unclassified_amount": round(cat_amt["UNC"], 2),
        "top_category": top, "top_category_share": round(cshare.get(top, 0), 3),
        # K5–K15
        "food_share": round(food, 3),
        "delivery_ratio": _pct(cat_amt["C1"], dsum),
        "small_txn_ratio": _pct(sum(a <= 20 for a in amts), n),
        "median_amount": round(statistics.median(amts), 2) if amts else 0,
        "big_ticket_share": _pct(sum(a for a in amts if a >= 200), total),
        "online_share": _pct(sum(t["amount"] for t in txns if t.get("is_online")), total),
        "shopping_share": round(cshare.get("C5", 0) + cshare.get("C6", 0), 3),
        "C4_share": round(cshare.get("C4", 0), 3), "C8_share": round(cshare.get("C8", 0), 3),
        "late_night_ratio": _pct(sum(t["is_late_night"] for t in txns), n),
        "beverage_per_week": round(cat_cnt["C4"] / weeks, 2),
        "commute_count_ratio": _pct(cat_cnt["C7"], n),
        "necessity_share": _pct(sum(t["amount"] for t in txns if t.get("is_necessity")), total),
        "weekend_share": _pct(sum(t["amount"] for t in txns if t["weekday"] >= 5), total),
        "front_loading": _pct(sum(t["amount"] for t in txns if (t["dt"].date() - period_start).days < 10), total) if period_start else 0.0,
        # K19–K27：16 张常规卡所需
        "C2_share": round(cshare.get("C2", 0), 3), "C3_share": round(cshare.get("C3", 0), 3),
        "C6_share": round(cshare.get("C6", 0), 3), "C9_share": round(cshare.get("C9", 0), 3),
        "C10_share": round(cshare.get("C10", 0), 3),
        "distinct_C2_merchants": len(c2_merchants),
        "game_share": _pct(game_amt, classified_total),
        "travel_share": _pct(travel_amt, classified_total),
        "subscription_brands": len(sub_brands),
        # K28–K33：特别卡与修饰标签所需
        "active_days_ratio": round(len(days) / period_days, 3),
        "max_day_share": _pct(day_amt[max_day], total) if max_day else 0.0,
        "max_day": str(max_day) if max_day else None,
        "max_day_txn_count": day_cnt[max_day] if max_day else 0,
        "discount_txn_ratio": _pct(sum(t["discount"] for t in txns), n),
        "transfer_count": report.get("R4_transfer", 0),
        "top_merchant_count_share": _pct(merchant_cnt.most_common(1)[0][1], n) if n else 0.0,
        "after_work_share": _pct(after_work, total),
        # 附加输出
        "top_merchants": [[mch, cnt] for mch, cnt in merchant_cnt.most_common(5)],
        "outliers": [{"id": t["id"], "date": t["time"][:10], "merchant": t["merchant"], "amount": t["amount"],
                      "category": t.get("category")} for t in txns if t["outlier"]],
        "ambiguous_count": sum(t["ambiguous"] for t in txns),
        "ambiguous_amount_share": _pct(sum(t["amount"] for t in txns if t["ambiguous"]), total),
        "ambiguous_rows": [{"date": t["time"][5:10], "merchant": t["merchant"], "amount": t["amount"], "category": t.get("category")}
                           for t in sorted((t for t in txns if t["ambiguous"]), key=lambda t: -t["amount"])[:3]],
        "masked_count": sum(t["masked"] for t in txns),
    }
    cats = {c for c in cat_cnt if c != "UNC"}
    if n < 10 or len(days) <= 1 or len(cats) <= 1:
        m["data_level"] = "不足"
    elif n >= 30 and len(days) >= 10 and len(cats) >= 3:
        m["data_level"] = "充足"
    else:
        m["data_level"] = "勉强"

    # VIP：K16–K18（仅当 M3 已写入 vip 字段）
    vip_rows = [t for t in txns if t.get("vip")]
    if vip_rows:
        food_rows = [t for t in vip_rows if t.get("category") in ("C1", "C2", "C3", "C4")]
        meal = Counter(t["vip"].get("meal_slot", "非餐饮") for t in food_rows)
        scene_amt = defaultdict(float)
        for t in vip_rows:
            scene_amt[t["vip"].get("scene", "未知")] += t["amount"]
        m["impulse_share"] = _pct(sum(t["amount"] for t in vip_rows if (t["vip"].get("impulse") or 0) >= 0.7), total)
        m["meal_slot_dist"] = {k: _pct(v, len(food_rows)) for k, v in meal.most_common()}
        m["scene_dist"] = {k: _pct(v, total) for k, v in sorted(scene_amt.items(), key=lambda x: -x[1])}
        m["late_meal_ratio"] = _pct(meal.get("夜宵", 0), len(food_rows))
        m["hour_hist"] = [0] * 24
        for t in txns:
            m["hour_hist"][t["hour"]] += 1
    m["petty_index"] = round(m["small_txn_ratio"] * min(1.0, m["txn_per_day"] / 4), 3)
    m.update(v4_metrics(txns, m, period_start, period_days, total, cat_amt, cat_cnt))
    m["dimensions"] = dimension_scores(m, vip=bool(vip_rows))
    m["highlights_candidates"] = highlights_candidates(txns, m)
    return m


def dim_score(value, anchors):
    """分段线性：anchors=[v0, v60, v100] → 0 / 60 / 100 分，两端截断。"""
    if value is None:
        return 0
    v0, v60, v100 = anchors
    if value <= v0:
        return 0
    if value <= v60:
        return round(60 * (value - v0) / (v60 - v0))
    if value >= v100:
        return 100
    return round(60 + 40 * (value - v60) / (v100 - v60))


def dimension_scores(m, vip=False):
    """11 维消费维度（VIP 加 ⚡ 冲动），每维 0–100；60 分 = 对应人格卡的 v1 阈值。"""
    out = {}
    for d in PERSONAS["dimensions"]:
        if d.get("vip_only") and not vip:
            continue
        out[d["id"]] = dim_score(m.get(d["metric"]), d["anchors"])
    return out


def _brief(t, kind, note=""):
    return {"id": t["id"], "kind": kind, "date": t["time"][5:10], "time": t["time"][11:16],
            "merchant": t["merchant"], "amount": t["amount"], "category": t.get("category"),
            "brand": (t.get("vip") or {}).get("brand"), "note": note}


def highlights_candidates(txns, m):
    """M6 只能从这里挑「高光时刻」：冲动最高 3 笔（VIP）、金额最大 3 笔、单日笔数最多的一天、最晚的一笔。"""
    if not txns:
        return []
    out, seen = [], set()

    def add(t, kind, note=""):
        if t["id"] not in seen:
            seen.add(t["id"]); out.append(_brief(t, kind, note))

    vip_rows = [t for t in txns if t.get("vip") and t["vip"].get("impulse") is not None]
    for t in sorted(vip_rows, key=lambda t: -t["vip"]["impulse"])[:3]:
        add(t, "impulse", f"冲动指数 {t['vip']['impulse']}")
    for t in sorted(txns, key=lambda t: -t["amount"])[:3]:
        add(t, "largest", "本月金额最大" if t["outlier"] else "大额")
    day_cnt = Counter(t["dt"].date() for t in txns)
    busiest, cnt = day_cnt.most_common(1)[0]
    rows = [t for t in txns if t["dt"].date() == busiest]
    big = max(rows, key=lambda t: t["amount"])
    add(big, "busiest_day", f"当天 {cnt} 笔，合计 ¥{sum(t['amount'] for t in rows):.2f}")
    # 最晚的一笔：22:00–05:59 之间，按「距 22 点的分钟数」排序
    def late_key(t):
        h = t["hour"] + t["dt"].minute / 60
        return h + 24 if h < 6 else h
    late = [t for t in txns if t["is_late_night"]]
    if late:
        add(max(late, key=late_key), "latest", "本月最晚一笔")
    return out


# ----------------------------------------------------------------------------- v4：人格条件所需指标（条件即维度）
def _hitkw(kws, text):
    tl = text.lower()
    return any(k.lower() in tl for k in kws)


def _groups_hit(groups, texts):
    hit = set()
    for name, kws in (groups or {}).items():
        if any(_hitkw(kws, x) for x in texts):
            hit.add(name)
    return hit


def _week_idx(t, period_start):
    return (t["dt"].date() - period_start).days // 7 if period_start else 0


def _meal_slot(h):
    if 5 <= h < 10: return "早餐"
    if 10 <= h < 14.5: return "午餐"
    if 16.5 <= h < 21: return "晚餐"
    if h >= 21 or h < 5: return "夜宵"
    return "下午茶"


def v4_metrics(txns, m, period_start, period_days, total, cat_amt, cat_cnt):
    import math
    from datetime import timedelta
    n = len(txns)
    weeks_total = max(1, math.ceil(period_days / 7))
    by = {}
    for t in txns:
        by.setdefault(t.get("category") or "UNC", []).append(t)
    cnt = lambda c: len(by.get(c, []))
    amt = lambda c: sum(t["amount"] for t in by.get(c, []))
    weeks = lambda rows: len({_week_idx(t, period_start) for t in rows})
    text = lambda t: t["merchant"] + " " + t["description"]
    fixed_amt = sum(t["amount"] for t in txns if t.get("fixed"))
    nonfixed = max(total - fixed_amt, 1e-9)
    food_amt = max(amt("C1") + amt("C2") + amt("C3") + amt("C4"), 1e-9)
    o = {"fixed_amount": round(fixed_amt, 2), "nonfixed_amount": round(total - fixed_amt, 2), "weeks_total": weeks_total}
    # 外卖
    c1 = by.get("C1", [])
    grocery = [t for t in by.get("C3", []) if not t.get("is_snack")]
    snacks = [t for t in by.get("C3", []) if t.get("is_snack")]
    o["delivery_cnt"] = len(c1)
    o["delivery_food_share"] = round(amt("C1") / food_amt, 3)
    o["weeks_C1"] = weeks(c1)
    o["delivery_meal_slots"] = len({_meal_slot(t["hour"] + t["dt"].minute / 60) for t in c1} - {"下午茶"})
    o["delivery_vs_grocery"] = round(len(c1) / max(1, len(grocery)), 2)
    # 茶饮
    c4 = by.get("C4", [])
    o["tea_cnt"] = len(c4); o["weeks_C4"] = weeks(c4); o["per_week_C4"] = round(len(c4) / weeks_total, 2)
    o["tea_max_repeat"] = max(Counter(t["merchant"] for t in c4).values()) if c4 else 0
    o["snack_cnt"] = len(snacks); o["tea_vs_snack"] = round(len(c4) / max(1, len(snacks)), 2)
    # 堂食
    c2 = by.get("C2", [])
    o["dinein_cnt"] = len(c2)
    o["c2_top_merchant_share"] = round(max(Counter(t["merchant"] for t in c2).values()) / len(c2), 3) if c2 else 0.0
    o["dinein_experience_share"] = round(sum(t["amount"] for t in c2 if t.get("rule_id") != "M02") / amt("C2"), 3) if c2 else 0.0
    # 网购（实物）：C5 全部 + 其他类别里渠道为线上的
    shop = [t for t in txns if t.get("category") == "C5" or (t.get("channel") == "online" and t.get("category") in ("C6", "C9", "C11", "C3"))]
    o["online_shop_cnt"] = len(shop); o["weeks_online_shop"] = weeks(shop)
    o["online_shop_nonfixed_share"] = round(sum(t["amount"] for t in shop) / nonfixed, 3)
    o["online_product_categories"] = len(_groups_hit(_MK.get("online_product_groups"), [t["description"] for t in shop]))
    o["online_distinct_merchants"] = len({t["merchant"] for t in shop})
    # 生鲜
    o["grocery_cnt"] = len(grocery); o["weeks_grocery"] = weeks(grocery)
    o["grocery_food_share"] = round(sum(t["amount"] for t in grocery) / food_amt, 3)
    o["grocery_categories"] = len(_groups_hit(_MK.get("grocery_groups"), [text(t) for t in grocery]))
    o["grocery_vs_delivery"] = round(len(grocery) / max(1, len(c1)), 2)
    # 美护
    c6 = by.get("C6", [])
    o["beauty_cnt"] = len(c6); o["weeks_C6"] = weeks(c6)
    o["beauty_nonfixed_share"] = round(amt("C6") / nonfixed, 3)
    o["beauty_categories"] = len(_groups_hit(_FAM["M10"].get("subtypes"), [text(t) for t in c6]))
    o["beauty_service_cnt"] = sum(1 for t in c6 if t.get("subtype") == "service" or _hitkw(_FAM["M10"]["subtypes"]["service"], text(t)))
    # 订阅 / 游戏 / 旅游（C8 内三分）
    c8 = by.get("C8", [])
    is_travel = lambda t: t.get("rule_id") == "M15" or t["platform_category"] == "酒店旅游" or t.get("brand_family") == "travel"
    is_sub = lambda t: t.get("rule_id") == "M14" or any(k in t["description"] for k in ("会员", "订阅", "连续包月", "Premium"))
    subs = [t for t in c8 if is_sub(t) and not is_travel(t)]
    travel = [t for t in c8 if is_travel(t)]
    games = [t for t in c8 if not is_travel(t) and not is_sub(t)]
    o["subscription_categories"] = len(_groups_hit(_FAM["M14"].get("subtypes"), [text(t) for t in subs]))
    digital = sum(t["amount"] for t in subs) + sum(t["amount"] for t in games)
    o["subscription_digital_share"] = round(sum(t["amount"] for t in subs) / digital, 3) if digital else 0.0
    o["game_cnt"] = len(games); o["weeks_game"] = weeks(games)
    o["game_entertainment_share"] = round(sum(t["amount"] for t in games) / amt("C8"), 3) if c8 else 0.0
    o["game_platform_max_repeat"] = max(Counter(t["merchant"] for t in games).values()) if games else 0
    o["virtual_item_cnt"] = sum(1 for t in txns if t.get("is_virtual_item"))
    tsub = lambda t: next((st for st, kws in _FAM["M15"]["subtypes"].items() if _hitkw(kws, text(t))), "other")
    tsubs = [(t, tsub(t)) for t in travel]
    o["travel_categories"] = len({s for _, s in tsubs if s != "other"})
    o["travel_nonfixed_share"] = round(sum(t["amount"] for t in travel) / nonfixed, 3)
    chain = 0
    for t, s in tsubs:
        if s == "long_transport":
            near = {s2 for t2, s2 in tsubs if abs((t2["dt"] - t["dt"]).days) <= 3}
            chain = max(chain, len(near - {"other"}))
    o["travel_chain"] = chain
    # 交通（城市）
    c7 = by.get("C7", [])
    o["commute_cnt"] = len(c7); o["weeks_C7"] = weeks(c7); o["per_week_C7"] = round(len(c7) / weeks_total, 2)
    o["commute_nonfixed_share"] = round(amt("C7") / nonfixed, 3)
    o["transport_modes"] = len({t.get("transport_mode") for t in c7 if t.get("transport_mode")})
    if period_start:
        wk_days = [period_start + timedelta(days=i) for i in range(period_days) if (period_start + timedelta(days=i)).weekday() < 5]
        c7_days = Counter(t["dt"].date() for t in c7)
        o["weekday_commute_ratio"] = round(sum(1 for d in wk_days if c7_days.get(d)) / len(wk_days), 3) if wk_days else 0.0
        o["days_with_2plus_commute"] = sum(1 for d, k in c7_days.items() if k >= 2)
    else:
        o["weekday_commute_ratio"] = 0.0; o["days_with_2plus_commute"] = 0
    # 宠物
    c11 = by.get("C11", [])
    o["pet_cnt"] = len(c11); o["weeks_C11"] = weeks(c11)
    o["pet_categories"] = len(_groups_hit(_FAM["M21"].get("subtypes"), [text(t) for t in c11]))
    o["pet_nonfixed_share"] = round(amt("C11") / nonfixed, 3)
    o["pet_max_repeat"] = max(Counter(t["merchant"] for t in c11).values()) if c11 else 0
    # 学习
    study = [t for t in by.get("C10", []) if t.get("is_study")]
    o["study_cnt"] = len(study); o["study_share"] = round(sum(t["amount"] for t in study) / total, 3) if total else 0.0
    top3 = [c for c, _ in sorted(((c, v) for c, v in cat_amt.items() if c != "UNC"), key=lambda x: -x[1])[:3]]
    o["study_cnt_or_top3"] = 1 if (len(study) >= 5 or ("C10" in top3 and study)) else 0
    o["early_cnt"] = sum(1 for t in txns if 5 <= t["hour"] < 8)
    # 金额模式
    o["under30_ratio"] = _pct(sum(1 for t in txns if t["amount"] < 30), n)
    o["big_nonnecessity_share"] = _pct(sum(t["amount"] for t in txns if t["amount"] >= 200 and not t.get("is_necessity")), total)
    day_nf = defaultdict(float); day_n = Counter()
    for t in txns:
        if not t.get("fixed"):
            day_nf[t["dt"].date()] += t["amount"]; day_n[t["dt"].date()] += 1
    streak = best = 0; prev = None
    for d in sorted(day_nf):
        ok = day_nf[d] <= 50 and day_n[d] >= 2          # 校准：只刷一次地铁的一天不算"过了一天 ≤ 50"
        streak = (streak + 1) if (ok and prev is not None and (d - prev).days == 1) else (1 if ok else 0)
        best = max(best, streak); prev = d
    o["daily_le50_streak"] = best
    wk_nf = defaultdict(float); wk_days = defaultdict(set)
    for d, v in day_nf.items():
        w = (d - period_start).days // 7 if period_start else 0
        wk_nf[w] += v; wk_days[w].add(d)
    o["weeks_le350"] = sum(1 for w, v in wk_nf.items() if v <= 350 and len(wk_days[w]) >= 4 and w < weeks_total)   # 校准：该周至少 4 个消费日
    # 深夜（21:00–04:59）
    late = [t for t in txns if t["is_late_night"]]
    o["late_night_cnt"] = len(late)
    late_days = Counter(t["dt"].date() for t in late)
    o["max_daily_late_cnt"] = max(late_days.values()) if late_days else 0
    o["days_with_3plus_late"] = sum(1 for k in late_days.values() if k >= 3)
    # 月度节奏
    if period_start:
        front = [t for t in txns if (t["dt"].date() - period_start).days < 10 and not t.get("fixed")]
        last = [t for t in txns if (t["dt"].date() - period_start).days >= period_days - 10 and not t.get("fixed")]
        fa, la = sum(t["amount"] for t in front), sum(t["amount"] for t in last)
        o["front10_days"] = len({t["dt"].date() for t in front}); o["last10_days"] = len({t["dt"].date() for t in last})
        o["last10_share"] = _pct(la, total); o["tail_vs_front"] = round(la / fa, 3) if fa else 1.0
    else:
        o.update(front10_days=0, last10_days=0, last10_share=0.0, tail_vs_front=1.0)
    # 商户集中
    loyal = [t for t in txns if t.get("category") != "C7" and not t.get("is_platform_merchant")]   # 一店死侍：排除交通与平台商户
    md = Counter((t["merchant"], t["dt"].date()) for t in loyal)
    o["merchant_max_daily_cnt"] = max(md.values()) if md else 0
    best = 0
    for mch in {t["merchant"] for t in loyal}:
        days = sorted(d for (m2, d), k in md.items() if m2 == mch and k >= 2)
        run = 0; prev = None
        for d in days:
            run = run + 1 if (prev is not None and (d - prev).days == 1) else 1
            best = max(best, run); prev = d
    o["merchant_streak_days"] = best
    mc = Counter(t["merchant"] for t in loyal)
    o["merchant_max_cnt_ex_platform"] = max(mc.values()) if mc else 0
    return o
