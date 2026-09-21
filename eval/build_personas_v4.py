# -*- coding: utf-8 -*-
"""从 docs_for_dev/人格设计/*.md（由 docx 转出）构建 rag/personas.json v4。

文案（一句话概括 / 解读 / 特点 / slogan / tone / do_not_say / guardrails / 插图）来自两份文档；
判定条件的指标映射（metric 名、阈值、方向、权重、是否需历史账单）在本文件 SPEC 中按文档逐条整理。
运行: python eval/build_personas_v4.py   （会保留旧 personas.json 的 dimensions / signature 供 B' 对照）
"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.normpath(os.path.join(HERE, ".."))
DOCS = os.path.join(ROOT, "docs_for_dev", "人格设计")
EMO = r"^[\U0001F300-\U0001FAFF☀-➿⭐]"


def _lines(name):
    return [l.rstrip() for l in open(os.path.join(DOCS, name), encoding="utf-8").read().splitlines() if l.strip()]


def _split_cn_en(s):
    m = re.match(r"^(.*?[。！？])\s*([A-Za-z\"“].*)$", s.strip())
    return (m.group(1).strip(), m.group(2).strip()) if m else (s.strip(), "")


def parse_doc1():
    L = _lines("MoneyBTI_人格设计1.md")
    heads = [i for i, l in enumerate(L) if re.match(EMO, l) and len(l) < 20]
    out = {}
    for n, i in enumerate(heads):
        seg = L[i:(heads[n + 1] if n + 1 < len(heads) else len(L))]
        name = re.sub(r"[“”\"]", "", seg[0]).strip()
        c = dict(name_raw=name, tagline="", tagline_en="", interp="", interp_en="", traits="", conditions=[], focus="",
                 distinguish=[], avoid="", guardrails=[], core="")
        mode = None
        for s in seg[1:]:
            key = s.split("：", 1)[0].split(":", 1)[0].strip()
            if key.startswith("一句话概括"):
                rest = s.split("：", 1)[1] if "：" in s else ""
                if rest.strip(): c["tagline"], c["tagline_en"] = _split_cn_en(rest)
                mode = "tagline"; continue
            if key == "人格解读":
                rest = s.split("：", 1)[1] if "：" in s else ""
                c["interp"] = rest.strip(); mode = "interp"; continue
            if key.startswith("人格特点"):
                rest = s.split("：", 1)[1] if "：" in s else ""
                c["traits"] = rest.strip(); mode = "traits"; continue
            if key.startswith("判定条件"): mode = None; continue
            if key.startswith("核心识别类别"): c["core"] = s.split("：", 1)[-1].strip(); continue
            if s.startswith("满足以下"): mode = "cond"; continue
            if key.startswith("侧重点"):
                c["focus"] = s.split("：", 1)[-1].strip() if "：" in s else ""; mode = "focus"; continue
            if key.startswith("与相似钱格的区分"):
                rest = s.split("：", 1)[-1].strip() if "：" in s else ""
                if rest: c["distinguish"].append(rest)
                mode = "dist"; continue
            if key.startswith("核心判定逻辑"): mode = "logic"; continue
            if key.startswith("Do Not Say"): mode = None; continue
            if key.startswith("Avoid Language"):
                rest = s.split("：", 1)[-1].strip() if "：" in s else ""
                if rest and rest != s: c["avoid"] = rest
                mode = "avoid"; continue
            if key.startswith("Generation Guardrails"): mode = "guard"; continue
            if mode == "tagline":
                if not c["tagline"]: c["tagline"], c["tagline_en"] = _split_cn_en(s)
                elif re.match(r"^[A-Za-z]", s) and not c["tagline_en"]: c["tagline_en"] = s
            elif mode == "interp":
                if re.match(r"^[A-Za-z]", s): c["interp_en"] = (c["interp_en"] + " " + s).strip()
                else: c["interp"] += s
            elif mode == "traits": c["traits"] = (c["traits"] + s).strip()
            elif mode == "cond": c["conditions"].append(s)
            elif mode == "focus": c["focus"] = (c["focus"] + " " + s).strip()
            elif mode == "dist": c["distinguish"].append(s)
            elif mode == "avoid": c["avoid"] = (c["avoid"] + s).strip()
            elif mode == "guard": c["guardrails"].append(s)
        out[re.sub(r"^[^A-Za-z一-鿿]+", "", name).strip()] = c
    return out


def parse_doc2():
    L = _lines("MoneyBTI_人格设计2.md")
    heads = [i for i, l in enumerate(L) if l.startswith(("人格名字", "新增人格名字"))]
    out = {}
    for n, i in enumerate(heads):
        seg = L[i:(heads[n + 1] if n + 1 < len(heads) else len(L))]
        raw = seg[0].split(":", 1)[-1].split("：", 1)[-1].strip()
        name = re.sub(r"[（(].*$", "", re.sub(r"^[^A-Za-z一-鿿]+", "", raw)).strip()
        c = dict(name_raw=raw, rules=[], core="", slogans=[], tone="", traits="", interp="", interp_en="", dns="", illustration=[])
        mode = None
        for s in seg[1:]:
            key = s.split(":", 1)[0].split("：", 1)[0].strip()
            rest = s.split(":", 1)[-1].split("：", 1)[-1].strip() if (":" in s or "：" in s) else ""
            if key.startswith("判定条件"): mode = "rule"; continue
            if key.startswith("核心识别类别"): mode = "core"; continue
            if key.startswith("一句话slogan"):
                if rest: c["slogans"].append(rest)
                mode = "slogan"; continue
            if key == "tone": c["tone"] = rest; mode = None; continue
            if key.startswith("人格特点"): mode = "traits"; continue
            if key.startswith("人格解读"): mode = "interp"; continue
            if key.startswith("Persona Interpretation"): mode = "interp_en"; continue
            if key == "do_not_say": c["dns"] = rest; mode = "dns"; continue
            if key == "illustration_prompt": mode = "illus"; continue
            if key == "slogan_examples":
                raw_rest = s.split(":", 1)[-1].strip()
                if "人格解读" in raw_rest:
                    sl = raw_rest.split("人格解读")[0].strip()
                    if sl: c["slogans"].append(sl)
                    c["interp"] += raw_rest.split("人格解读", 1)[1].lstrip("：: "); mode = "interp"
                else:
                    if raw_rest: c["slogans"].append(raw_rest)
                    mode = "slogan"
                continue
            if mode == "rule": c["rules"].append(s)
            elif mode == "core": c["core"] += s
            elif mode == "slogan": c["slogans"].append(s)
            elif mode == "traits": c["traits"] += s
            elif mode == "interp":
                if re.match(r"^[A-Za-z]", s): c["interp_en"] += s; mode = "interp_en"
                else: c["interp"] += s
            elif mode == "interp_en": c["interp_en"] = (c["interp_en"] + " " + s).strip()
            elif mode == "dns": c["dns"] += s
            elif mode == "illus": c["illustration"].append(s)
        out[name] = c
    return out


# ----------------------------------------------------------------------------- 条件规格（按文档逐条整理）
def C(id, label, metric, op, value, w=1, history=False, note=""):
    d = {"id": id, "label": label, "metric": metric, "op": op, "value": value, "weight": w}
    if history: d["requires_history"] = True
    if note: d["note"] = note
    return d


SPEC = {
 # ---- 文档 1：满足 ≥ 3 条（可用条件不足 5 条时按比例，见 retrieve.py）
 "外卖包月户": dict(code="WMBY", emoji="🥡", axis="类别·外卖", rarity="常见", mode="count", conditions=[
    C("freq", "外卖订单 ≥ 12 次", "delivery_cnt", ">=", 12, w=2),
    C("share", "外卖占餐饮支出 ≥ 50%", "delivery_food_share", ">=", 0.50),
    C("persist", "至少 3 周出现外卖", "weeks_C1", ">=", 3, w=2),
    C("scenes", "覆盖 ≥ 2 个餐次", "delivery_meal_slots", ">=", 2),
    C("vs_grocery", "外卖笔数明显高于生鲜（≥ 1.5 倍）", "delivery_vs_grocery", ">=", 1.5)]),
 "奶茶续命体": dict(code="NCXM", emoji="🥤", axis="类别·饮品", rarity="常见", mode="count", conditions=[
    C("freq", "现制茶饮 ≥ 8 次", "tea_cnt", ">=", 8, w=2),
    C("persist", "至少 3 周出现茶饮", "weeks_C4", ">=", 3),
    C("per_week", "每周茶饮 ≥ 2 次", "per_week_C4", ">=", 2),
    C("repeat", "同一茶饮商户复购 ≥ 3 次", "tea_max_repeat", ">=", 3),
    C("vs_snack", "茶饮笔数明显高于零食甜品（≥ 1.5 倍）", "tea_vs_snack", ">=", 1.5)]),
 "探店雷达": dict(code="TDLD", emoji="🍴", axis="类别·堂食", rarity="少见", mode="count", conditions=[
    C("freq", "线下餐饮 ≥ 8 次", "dinein_cnt", ">=", 8),
    C("diversity", "≥ 6 家不同餐饮商户", "distinct_C2_merchants", ">=", 6, w=2),
    C("new_rate", "新店率 ≥ 50%（需历史账单）", "new_store_rate", ">=", 0.5, history=True),
    C("low_repeat", "单一商户 ≤ 30% 的堂食笔数", "c2_top_merchant_share", "<=", 0.30),
    C("experience", "非快餐连锁占线下餐饮 ≥ 40%", "dinein_experience_share", ">=", 0.40)]),
 "快递召唤师": dict(code="KDZH", emoji="🛍️", axis="类别·网购", rarity="常见", mode="count", conditions=[
    C("freq", "实物网购订单 ≥ 10 笔", "online_shop_cnt", ">=", 10, w=2),
    C("persist", "至少 3 周有网购", "weeks_online_shop", ">=", 3, w=2),
    C("share", "网购占非固定消费 ≥ 25%", "online_shop_nonfixed_share", ">=", 0.25),
    C("categories", "覆盖 ≥ 3 个商品品类", "online_product_categories", ">=", 3),
    C("merchants", "≥ 3 个不同商户 / 品牌", "online_distinct_merchants", ">=", 3)]),
 "菜场理财家": dict(code="CCLJ", emoji="🌽", axis="类别·生鲜", rarity="少见", mode="count", conditions=[
    C("freq", "食材消费 ≥ 8 次", "grocery_cnt", ">=", 8, w=2),
    C("persist", "至少 3 周采购食材", "weeks_grocery", ">=", 3, w=2),
    C("share", "食材占餐饮支出 ≥ 30%", "grocery_food_share", ">=", 0.30),
    C("categories", "食材覆盖 ≥ 3 类", "grocery_categories", ">=", 3),
    C("vs_delivery", "食材笔数明显高于外卖（≥ 1.5 倍）", "grocery_vs_delivery", ">=", 1.5)]),
 "精致主义者": dict(code="JZZY", emoji="💄", axis="类别·美妆服饰", rarity="常见", mode="count", conditions=[
    C("freq", "品质 / 形象类消费 ≥ 6 次", "beauty_cnt", ">=", 6),
    C("share", "占非固定支出 ≥ 20%", "beauty_nonfixed_share", ">=", 0.20, w=2),
    C("categories", "覆盖 ≥ 3 个品质类别", "beauty_categories", ">=", 3, w=2),
    C("persist", "至少 3 周出现", "weeks_C6", ">=", 3),
    C("service", "美发 / 美甲 / 美容服务 ≥ 2 次", "beauty_service_cnt", ">=", 2)]),
 "订阅收藏家": dict(code="DYSJ", emoji="📱", axis="类别·订阅", rarity="少见", mode="count", conditions=[
    C("count", "≥ 5 个不同订阅服务", "subscription_brands", ">=", 5, w=2),
    C("periodic", "同一商户规律扣费（需历史账单）", "subscription_periodic", ">=", 1, history=True),
    C("categories", "订阅覆盖 ≥ 3 个类别", "subscription_categories", ">=", 3),
    C("streak", "≥ 3 项连续扣费 3 个周期（需历史账单）", "subscription_streak3", ">=", 3, history=True),
    C("share", "订阅占数字服务消费 ≥ 40%", "subscription_digital_share", ">=", 0.40)]),
 "氪金战士": dict(code="KJZS", emoji="🎮", axis="类别·游戏", rarity="少见", mode="count", conditions=[
    C("freq", "游戏充值 / 内购 ≥ 5 次", "game_cnt", ">=", 5, w=2),
    C("persist", "至少 3 周出现游戏付费", "weeks_game", ">=", 3),
    C("share", "游戏占娱乐类消费 ≥ 30%", "game_entertainment_share", ">=", 0.30, w=2),
    C("repeat", "同一游戏 / 平台 ≥ 3 笔", "game_platform_max_repeat", ">=", 3),
    C("virtual", "点券 / 皮肤 / 通行证等虚拟内容 ≥ 3 笔", "virtual_item_cnt", ">=", 3)]),
 "地球online玩家": dict(code="DQOL", emoji="🌍", axis="类别·旅游", rarity="少见", mode="count", conditions=[
    C("episodes", "≥ 2 次独立旅行周期（文档为 90 天，需历史账单）", "travel_episodes_90d", ">=", 2, history=True),
    C("categories", "覆盖交通 / 住宿 / 门票 ≥ 3 类", "travel_categories", ">=", 3, w=2),
    C("share", "旅行占非固定消费 ≥ 15%", "travel_nonfixed_share", ">=", 0.15, w=2),
    C("chain", "长途交通 + 住宿 / 门票的消费链 ≥ 2 类", "travel_chain", ">=", 2),
    C("cross_region", "≥ 2 个异地城市（需位置信息）", "travel_cross_region", ">=", 2, history=True)]),
 "通勤永动机": dict(code="TQYD", emoji="🚇", axis="类别·交通", rarity="常见", mode="count", conditions=[
    C("freq", "城市交通 ≥ 20 笔", "commute_cnt", ">=", 20, w=2),
    C("persist", "每周都有交通消费（≥ 4 周）", "weeks_C7", ">=", 4, w=2),
    C("per_week", "每周交通 ≥ 5 次", "per_week_C7", ">=", 5),
    C("share", "交通占日常可变支出 ≥ 10%", "commute_nonfixed_share", ">=", 0.10),
    C("modes", "≥ 2 种交通方式", "transport_modes", ">=", 2),
    C("regular", "工作日中 ≥ 60% 有交通记录", "weekday_commute_ratio", ">=", 0.60)]),
 "毛孩子提款机": dict(code="MHZT", emoji="🐱", axis="类别·宠物", rarity="少见", mode="count", conditions=[
    C("freq", "宠物相关消费 ≥ 5 笔", "pet_cnt", ">=", 5, w=2),
    C("persist", "至少 3 周出现宠物消费", "weeks_C11", ">=", 3, w=2),
    C("categories", "覆盖食品 / 用品 / 医疗 / 服务 ≥ 2 类", "pet_categories", ">=", 2),
    C("share", "宠物占非固定支出 ≥ 10%", "pet_nonfixed_share", ">=", 0.10),
    C("repeat", "同一宠物商户复购 ≥ 2 次", "pet_max_repeat", ">=", 2),
    C("months", "连续 ≥ 3 个月（需历史账单）", "pet_months_streak", ">=", 3, history=True)]),
 # ---- 文档 2：任一规则组全部满足
 "卷王": dict(code="JW", emoji="📚", axis="类别·学习", rarity="少见", mode="any", rule_groups=[
    [C("share20", "学习类占总消费 ≥ 20%", "study_share", ">=", 0.20, w=2), C("cnt_or_top3", "学习类 ≥ 5 笔或进入前三", "study_cnt_or_top3", ">=", 1)],
    [C("share30", "学习类占总消费 ≥ 30%", "study_share", ">=", 0.30, w=2), C("n3", "有效交易 > 3 笔", "txn_count", ">", 3)],
    [C("early", "05:00–08:00 消费 ≥ 15 笔", "early_cnt", ">=", 15, w=2), C("study5", "学习类 ≥ 5 笔", "study_cnt", ">=", 5)]]),
 "壕": dict(code="HAO", emoji="👑", axis="金额·大额", rarity="稀有", mode="any", rule_groups=[
    [C("median", "单笔中位数 ≥ ¥70", "median_amount", ">=", 70, w=2), C("big", "大额消费占比 ≥ 40%", "big_ticket_share", ">=", 0.40, w=2),
     C("top", "最大类别 ∈ 网购 / 美妆服饰 / 堂食", "top_category", "in", ["C5", "C6", "C2"]), C("n10", "≥ 10 笔", "txn_count", ">=", 10)]]),
 "散财童子": dict(code="SCTZ", emoji="💸", axis="金额·小额高频", rarity="常见", mode="any", rule_groups=[
    [C("per_day", "日均 ≥ 3 笔", "txn_per_day", ">=", 3), C("small60", "小额（≤ ¥20）≥ 60%", "small_txn_ratio", ">=", 0.60, w=2),
     C("top30", "最大类别 < 30%", "top_category_share", "<", 0.30)],
    [C("under30", "< ¥30 的笔数 ≥ 50%", "under30_ratio", ">=", 0.50, w=2), C("per_day25", "且日均 ≥ 2.5 笔（校准加：区分省钱大师）", "txn_per_day", ">=", 2.5)]]),
 "省钱大师": dict(code="SQDS", emoji="🐿️", axis="金额·低消费", rarity="少见", mode="any", rule_groups=[
    [C("necessity", "必需消费 ≥ 60%", "necessity_share", ">=", 0.60, w=2), C("median", "中位数 ≤ ¥30", "median_amount", "<=", 30),
     C("big_nonnec", "大额非必需 ≤ 15%", "big_nonnecessity_share", "<=", 0.15)],
    [C("daily50", "日消费 ≤ ¥50 连续 ≥ 3 天（剔除固定支出，每天 ≥ 2 笔）", "daily_le50_streak", ">=", 3, w=2)],
    [C("weekly350", "周消费 ≤ ¥350 的周数 ≥ 2（剔除固定支出，该周 ≥ 4 个消费日）", "weeks_le350", ">=", 2, w=2)]]),
 "夜行动物": dict(code="YXDW", emoji="🌙", axis="时间·深夜", rarity="少见", mode="any", rule_groups=[
    [C("ratio", "21:00–05:00 笔数占比 ≥ 30%", "late_night_ratio", ">=", 0.30, w=2), C("n10", "> 10 笔", "txn_count", ">", 10)],
    [C("cnt15", "深夜笔数 ≥ 15", "late_night_cnt", ">=", 15, w=2), C("ratio15", "且深夜占比 ≥ 15%（校准加）", "late_night_ratio", ">=", 0.15)],
    [C("daily3", "某日深夜 ≥ 3 笔", "max_daily_late_cnt", ">=", 3, w=2), C("days2", "且这样的天数 ≥ 2（校准加）", "days_with_3plus_late", ">=", 2)]]),
 "月底渡劫人": dict(code="YDDJ", emoji="🥀", axis="时间·月度节奏", rarity="稀有", group="special", override=False, mode="any", rule_groups=[
    [C("front", "前 10 天 ≥ 50%", "front_loading", ">=", 0.50, w=2), C("tail", "后 10 天 ≤ 前 10 天的 50%", "tail_vs_front", "<=", 0.50, w=2),
     C("front_days", "前 10 天 ≥ 5 个消费日", "front10_days", ">=", 5), C("tail_days", "后 10 天 ≥ 5 个消费日", "last10_days", ">=", 5)]]),
 "社交能手": dict(code="SJNS", emoji="🧧", axis="成就·社交", rarity="稀有", group="special", override=True, mode="any", rule_groups=[
    [C("transfers", "转账 / 红包 ≥ 10 笔（不计入消费）", "transfer_count", ">=", 10, w=2)]]),
 "一店死侍": dict(code="YDSS", emoji="❤️", axis="成就·专一", rarity="稀有", group="special", override=True, override_groups=[0], mode="any", rule_groups=[
    [C("share50", "单一商户占笔数 ≥ 50%", "top_merchant_count_share", ">=", 0.50, w=2), C("n20", "≥ 20 笔", "txn_count", ">=", 20)],
    [C("daily4", "某日同一商户 ≥ 4 笔（排除交通与平台）", "merchant_max_daily_cnt", ">=", 4, w=2)],
    [C("streak", "连续 ≥ 3 天同一商户每日 ≥ 2 笔（排除交通与平台）", "merchant_streak_days", ">=", 3, w=2)],
    [C("month30", "同一商户月 ≥ 30 笔（排除外卖 / 电商平台）", "merchant_max_cnt_ex_platform", ">=", 30, w=2)]]),
 "端水大师": dict(code="DSDS", emoji="🐙", axis="兜底·均衡", rarity="少见", group="fallback", mode="fallback", rule_groups=[
    [C("no_hit", "无其他人格命中", "rule_hits", "==", 0), C("top30", "最大类别 < 30%", "top_category_share", "<", 0.30)]]),
 "数据无法捕获之人": dict(code="SJWF", emoji="🕵️", axis="兜底·数据不足", rarity="传说", group="fallback", mode="fallback", rule_groups=[
    [C("level", "数据充足度 = 不足", "data_level", "==", "不足")]]),
}

# 全勤打工人 → 徽章；一日暴走 / 薅羊毛 沿用 v3 触发
BADGES = [
 {"code": "QQDK", "name": "全勤打工人", "emoji": "🏆", "trigger": [{"metric": "active_days_ratio", "op": ">=", "value": 0.90}, {"metric": "period_days", "op": ">=", "value": 28}],
  "trigger_any": [[{"metric": "active_days_ratio", "op": ">=", "value": 0.90}, {"metric": "period_days", "op": ">=", "value": 28}],
                  [{"metric": "days_with_2plus_commute", "op": ">=", "value": 22}], [{"metric": "commute_cnt", "op": ">=", "value": 50}]],
  "line": "人全勤，钱包也全勤。", "slogan": "31 DAYS. 31 RECEIPTS. PERFECT ATTENDANCE."},
 {"code": "YRBZ", "name": "一日暴走", "emoji": "🎰", "trigger_any": [[{"metric": "max_day_share", "op": ">=", "value": 0.5}, {"metric": "max_day_txn_count", "op": ">=", "value": 5}, {"metric": "txn_count", "op": ">=", "value": 10}]],
  "line": "平时很省，直到那一天。", "slogan": "ONE DAY. ALL IN."},
 {"code": "HYM", "name": "薅羊毛大师", "emoji": "🐑", "trigger_any": [[{"metric": "discount_txn_ratio", "op": ">=", "value": 0.2}, {"metric": "txn_count", "op": ">=", "value": 20}]],
  "line": "没有优惠的订单不配被支付。", "slogan": "COUPON FIRST. PAY LATER."},
]

OLD2NEW = {"BKHZ": "WMBY", "NCXM": "NCXM", "TDJ": "TDLD", "MCDR": "CCLJ", "WGKR": "KDZH", "JZZY": "JZZY", "KJZS": "KJZS", "DYSJ": "DYSJ",
           "SZJZ": "DQOL", "TQDG": "TQYD", "JW": "JW", "HAO": "HAO", "SCTZ": "SCTZ", "SQDS": "SQDS", "YXDW": "YXDW",
           "RQWL": "SJNS", "ZYX": "YDSS", "LBX": "DSDS", "SMR": "SJWF"}


def splitlist(s):
    return [x.strip(" 、，,。") for x in re.split(r"[/、，,｜|]", s) if x.strip(" 、，,。")]


def main():
    d1, d2 = parse_doc1(), parse_doc2()
    old_path = os.path.join(ROOT, "rag", "personas_v3_backup.json")          # v3 知识库：dimensions 与 signature 的来源
    old = json.load(open(old_path, encoding="utf-8"))
    old_by_code = {c["code"]: c for c in old["cards"]}
    sigs = {OLD2NEW[c]: old_by_code[c].get("signature") for c in OLD2NEW if old_by_code.get(c, {}).get("signature")}
    cards = []
    for name, spec in SPEC.items():
        src = d1.get(name) or d2.get(name)
        assert src, name
        code = spec["code"]
        card = {"code": code, "name": name, "emoji": spec["emoji"], "group": spec.get("group", "regular"), "axis": spec["axis"],
                "rarity": spec["rarity"], "override": spec.get("override", False), "mode": spec["mode"]}
        if spec.get("override_groups") is not None: card["override_groups"] = spec["override_groups"]
        if spec["mode"] == "count":
            card["conditions"] = spec["conditions"]; card["min_conditions"] = 3
        else:
            card["rule_groups"] = spec["rule_groups"]
        if name in d1:
            s = d1[name]
            card.update(tagline=s["tagline"], tagline_en=s["tagline_en"], interpretation=s["interp"], interpretation_en=s["interp_en"],
                        traits=splitlist(s["traits"]), core_categories=s["core"], focus=s["focus"], distinguish=s["distinguish"],
                        tone="轻松、有共鸣、不带消费羞辱", slogan_examples=[s["tagline_en"]] if s["tagline_en"] else [],
                        do_not_say=splitlist(s["avoid"]), guardrails=s["guardrails"], illustration_prompt="")
        else:
            s = d2[name]
            cn = [x for x in s["slogans"] if re.search(r"[一-鿿]", x)]
            en = [x for x in s["slogans"] if not re.search(r"[一-鿿]", x)]
            card.update(tagline=cn[0] if cn else "", tagline_en=en[0] if en else "", interpretation=s["interp"], interpretation_en=s["interp_en"],
                        traits=splitlist(s["traits"]), core_categories=s["core"], focus="", distinguish=[],
                        tone=s["tone"] or "轻松、调侃", slogan_examples=en, slogan_examples_cn=cn[1:],
                        do_not_say=splitlist(s["dns"]), guardrails=[], illustration_prompt=s["illustration"][0] if s["illustration"] else "",
                        rules_text=s["rules"])
        card["summary_examples"] = [x for x in [card["tagline"], card["interpretation"][:60]] if x]
        if code in sigs: card["signature"] = sigs[code]        # v3 原型，仅供评估对照 B'
        cards.append(card)
    dims = old["dimensions"]
    for d in dims:
        if d["id"] == "night": d["anchors"] = [0, 0.30, 0.60]; d["desc"] = "21:00–04:59 笔数占比"
    tags = [t for t in old["modifier_tags"] if "月初" not in t["tag"]]
    kb = {"_meta": {"version": "4.0", "date": "2026-09-10",
                    "description": ("MoneyBTI 钱格 人格卡知识库 v4。22 张卡来自组员的《人格设计 1 / 2》：类别型 11 张用 mode=count（5 条条件满足 ≥ 3 条即命中；"
                                    "需历史账单的条件在单月数据上不计入分母），金额 / 时间 / 特别 / 兜底 11 张用 mode=any（任一规则组全部满足）。"
                                    "每条条件按分段线性打成 0–100 分（阈值 = 60 分），卡匹配度 = 条件分的加权平均（条件即维度）。"
                                    "special 卡 override=true 时命中即主人格；月底渡劫人 special 但不覆盖，作为并列人格。全勤 / 一日暴走 / 薅羊毛为成就徽章，不作人格。"
                                    "signature 字段是 v3 的 12 维原型，只用于评估对照 B'。"),
                    "categories_note": "C11 宠物 为 v4 新增类别", "rarity_levels": old["_meta"]["rarity_levels"]},
          "dimensions": dims, "cards": cards, "badges": BADGES, "modifier_tags": tags}
    # ---- 合并英文翻译（rag/personas_en.json，由 eval/translate_kb.py 生成）
    en_path = os.path.join(ROOT, "rag", "personas_en.json")
    if os.path.exists(en_path):
        en = json.load(open(en_path, encoding="utf-8"))
        for card in kb["cards"]:
            e = en["cards"].get(card["code"])
            if not e: continue
            card["name_en"] = e.get("name", card["name"]); card["axis_en"] = e.get("axis", ""); card["tone_en"] = e.get("tone", "")
            card["traits_en"] = e.get("traits", []); card["core_categories_en"] = e.get("core_categories", "")
            card["do_not_say_en"] = e.get("do_not_say", []); card["guardrails_en"] = e.get("guardrails", [])
            card["distinguish_en"] = e.get("distinguish", []); card["focus_en"] = e.get("focus", "")
            if not card.get("interpretation_en") and e.get("interpretation"): card["interpretation_en"] = e["interpretation"]
            if not card.get("tagline_en") and e.get("tagline"): card["tagline_en"] = e["tagline"]
            labels = list(e.get("condition_labels", []))
            conds = card["conditions"] if card["mode"] == "count" else [c for g in card.get("rule_groups", []) for c in g]
            for c, lab in zip(conds, labels): c["label_en"] = lab
        for b in kb["badges"]:
            e = en["badges"].get(b["code"])
            if e: b["name_en"] = e.get("name", b["name"]); b["line_en"] = e.get("line", "")
        DIM_EN = {"eat": "Food", "delivery": "Delivery", "drink": "Drinks", "shopping": "Shopping", "online": "Online", "fun": "Fun",
                  "commute": "On the move", "practical": "Essentials", "lavish": "Big-ticket", "petty": "Petty", "night": "Night owl", "impulse": "Impulse"}
        for d in kb["dimensions"]: d["name_en"] = DIM_EN.get(d["id"], d["name"])
        kb["_meta"]["i18n"] = "字段 *_en 为英文版（名称取设计稿英文名，其余由 eval/translate_kb.py 翻译后人工抽查）；M6 / M7 按 lang 参数选用中文或英文字段。"
    json.dump(kb, open(os.path.join(ROOT, "rag", "personas.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("cards:", len(cards), "| badges:", len(BADGES), "| tags:", len(tags))
    for c in cards:
        miss = [k for k in ("tagline", "interpretation", "interpretation_en", "do_not_say") if not c.get(k)]
        print(f"  {c['code']:5} {c['emoji']}{c['name']:8} {c['group']:8} {c['mode']:8} cond={len(c.get('conditions', []))} groups={len(c.get('rule_groups', []))} "
              f"tag={c['tagline'][:14]!r} dns={len(c['do_not_say'])} guard={len(c.get('guardrails', []))} {'MISSING ' + ','.join(miss) if miss else ''}")


if __name__ == "__main__":
    main()
