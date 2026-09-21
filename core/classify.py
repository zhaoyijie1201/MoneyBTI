# -*- coding: utf-8 -*-
"""M2 商户映射（普通版规则）v2：negations → 平台穿透 → L1 商户名 → L2 平台分类 → L3 说明关键词 → 未分类。
平台穿透：商户是外卖 / 电商平台时，先用商品说明匹配品牌家族（茶饮、咖啡、宠物、游戏、订阅、零食、生鲜、服饰美妆），
命中则按品牌类别，平台只记为渠道——"具体消费类别 > 消费渠道"。同时给每笔交易打 subtype / fixed / channel 标记，供 M5 指标使用。
"""
from collections import Counter
from .kb import RULES, DEFAULTS

_FAM = {f["id"]: f for f in RULES["L1_merchant_families"]}
_PASS = RULES.get("platform_passthrough", {"platform_families": [], "brand_families": []})
_FIXED = RULES.get("fixed_cost_keywords", [])
_MK = RULES.get("metric_keywords", {})

UNCLASSIFIED = {"category": None, "layer": "unclassified", "rule_id": None, "keyword": None,
                "is_online": False, "is_necessity": False, "channel": None, "subtype": None}


def _hit(keywords, text):
    tl = text.lower()
    for k in keywords:
        if k.lower() in tl:
            return k
    return None


def _subtype(fam, text):
    for st, kws in (fam.get("subtypes") or {}).items():
        if _hit(kws, text):
            return st
    return None


def _result(category, layer, rule_id, keyword=None, is_online=None, is_necessity=None, channel=None, subtype=None):
    d = DEFAULTS[category]
    return {"category": category, "layer": layer, "rule_id": rule_id, "keyword": keyword,
            "is_online": d["is_online"] if is_online is None else is_online,
            "is_necessity": d["is_necessity"] if is_necessity is None else is_necessity,
            "channel": channel, "subtype": subtype}


def classify_basic(t):
    """返回 dict(category|None, layer, rule_id, keyword, is_online, is_necessity, channel, subtype)。"""
    m, d, pc = t["merchant"], t["description"], t["platform_category"]
    for n in RULES["negations"]:
        k = _hit(n["keywords"], m + " " + d)
        if k:
            return _result(n["category"], "N", n["id"], k)
    # 平台穿透：外卖 / 电商平台 + 说明里的品牌
    plat = None
    for fid in _PASS.get("platform_families", []):
        if _hit(_FAM[fid]["keywords"], m):
            plat = fid; break
    if plat and d:
        for fid in _PASS.get("brand_families", []):
            fam = _FAM[fid]
            k = _hit(fam["keywords"], d)
            if k:
                channel = "delivery" if plat == "M01" else "online"
                return _result(fam["category"], "L1d", fam["id"], k, True, fam["is_necessity"], channel, _subtype(fam, d))
    for fam in RULES["L1_merchant_families"]:
        k = _hit(fam["keywords"], m)
        if k:
            channel = "delivery" if fam["id"] == "M01" else ("online" if fam["id"] in ("M08", "M09") else None)
            return _result(fam["category"], "L1", fam["id"], k, fam["is_online"], fam["is_necessity"], channel, _subtype(fam, m + " " + d))
    l2 = RULES["L2_alipay_category_map"].get(pc)
    if l2 and l2.get("needs_L3_first"):
        for kw in RULES["L3_description_keywords"]:
            k = _hit(kw["keywords"], d)
            if k:
                return _result(kw["category"], "L3", "L3", k)
    if l2 and l2["category"]:
        return _result(l2["category"], "L2", pc, pc)
    for kw in RULES["L3_description_keywords"]:
        k = _hit(kw["keywords"], d)
        if k:
            return _result(kw["category"], "L3", "L3", k)
    return dict(UNCLASSIFIED)


def tag_flags(t):
    """与类别无关的标记：fixed（固定生活支出）、transport_mode、is_snack、is_virtual_item、is_study。"""
    text = t["merchant"] + " " + t["description"]
    t["fixed"] = bool(_hit(_FIXED, text)) or t.get("rule_id") == "M17"
    modes = _MK.get("transport_modes", {})
    t["transport_mode"] = next((mode for mode, kws in modes.items() if _hit(kws, text)), None) if t.get("category") == "C7" else None
    t["is_snack"] = bool(_hit(_MK.get("snack", []), text)) if t.get("category") == "C3" else False
    t["is_virtual_item"] = bool(_hit(_MK.get("virtual_item", []), text))
    t["is_study"] = t.get("category") == "C10" and (t.get("rule_id") == "M19" or t["platform_category"] == "教育培训" or bool(_hit(_MK.get("study", []), text)))
    t["is_platform_merchant"] = t.get("rule_id") in ("M01", "M08", "M09") or t.get("layer") == "L1d"


def apply_basic(txns):
    """就地给每笔交易写入 category / is_online / is_necessity / layer / rule_id / rule_keyword / channel / subtype /
    source_of_label / confidence 与 tag_flags。返回各层命中计数。普通版命中即定案；VIP 版把 category 作为 rule_label 送 M3。"""
    layers = Counter()
    for t in txns:
        r = classify_basic(t)
        t.update(category=r["category"], is_online=r["is_online"], is_necessity=r["is_necessity"],
                 layer=r["layer"], rule_id=r["rule_id"], rule_keyword=r["keyword"], channel=r["channel"], subtype=r["subtype"])
        t["source_of_label"] = ("rule_" + r["layer"]) if r["category"] else None
        t["confidence"] = 1.0 if r["category"] else 0.0
        tag_flags(t)
        layers[r["layer"]] += 1
    return dict(layers)


def apply_user_labels(txns, overrides):
    """M4 Human review：overrides = {txn_id: category}。用户确认的类别覆盖规则 / LLM 结果。"""
    by_id = {t["id"]: t for t in txns}
    for tid, cat in overrides.items():
        t = by_id.get(tid)
        if t is None or cat not in DEFAULTS:
            continue
        t["category"] = cat
        t["is_online"] = DEFAULTS[cat]["is_online"]
        t["is_necessity"] = DEFAULTS[cat]["is_necessity"]
        t["source_of_label"] = "user"
        t["confidence"] = 1.0
        tag_flags(t)
    return txns
