# -*- coding: utf-8 -*-
"""
MoneyBTI 钱格 · 规则检索参考实现 (Stage 4 RAG) —— 兼容入口

实现已迁到 core/ 包 (parser / classify / metrics / retrieve)，本文件只保留同名函数导出与 CLI 演示：
  classify_basic(txn)        普通版三层商户映射: negations → L1 → L2 → L3 → 未分类
  compute_metrics(txns)      K1–K33 指标 (代码计算, 不经 LLM)
  retrieve_personas(metrics) 人格卡候选检索: 阈值匹配 + 匹配强度排序, 返回 2–3 张卡
  parse_bill(path)           支付宝 CSV / 微信 xlsx 解析 (M1)

运行:  python rag/retrieval.py [data/*.csv data/*.xlsx]
输出只包含聚合数字, 不打印任何个人信息。
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..")))

from core import parse_bill, classify_basic, compute_metrics, retrieve_personas, analyze_rules  # noqa: E402
from core.kb import RULES, PERSONAS, DEFAULTS  # noqa: E402,F401


def run(path):
    r = analyze_rules(path)
    m, ret, report = r["metrics"], r["retrieval"], r["report"]
    name = re.sub(r"^[A-Za-z]+", "", os.path.basename(path))  # 去掉文件名前缀里可能的人名缩写
    print("=" * 78)
    print("账单:", name[:40], "| 来源:", report["source"], "| 周期:", report["period_start"], "~", report["period_end"],
          f"({report['period_days']} 天{'' if report['period_from_header'] else ', 首末交易推算'})")
    print("清洗:", {k: v for k, v in report.items() if k.startswith(("R", "bad", "raw", "valid"))})
    print("规则命中层:", r["layers"], "| 覆盖率:", f"{(1 - m['unclassified_ratio']) * 100:.1f}%")
    print("指标:", {k: m[k] for k in ("total", "txn_count", "txn_per_day", "top_category", "top_category_share",
                                     "food_share", "delivery_ratio", "small_txn_ratio", "median_amount",
                                     "big_ticket_share", "online_share", "C8_share", "commute_count_ratio",
                                     "necessity_share", "late_night_ratio", "front_loading", "data_level")})
    print("类别占比:", m["category_share"])
    print("特别卡指标:", {k: m[k] for k in ("period_days", "active_days_ratio", "max_day_share", "max_day_txn_count",
                                          "discount_txn_ratio", "transfer_count", "top_merchant_count_share",
                                          "subscription_brands", "travel_share", "distinct_C2_merchants")})
    print("人格候选 (code, match, hit):", [(c["code"], c["match"], c["hit"]) for c in ret["candidates"]],
          "| 常规命中数:", ret["hits"], "| 特别卡:", ret["special"], "| 徽章:", [b["code"] for b in ret["badges"]], "| 标签:", ret["modifier_tags"])
    print("维度分:", m["dimensions"])
    print("高光候选:", [(h["kind"], h["date"], h["amount"]) for h in m["highlights_candidates"]])


if __name__ == "__main__":
    data_dir = os.path.join(HERE, "..", "data")
    files = sys.argv[1:] or [os.path.join(data_dir, f) for f in sorted(os.listdir(data_dir))
                             if f.endswith((".csv", ".xlsx")) and not f.startswith("~$")]
    for f in files:
        run(f)
