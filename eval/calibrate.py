# -*- coding: utf-8 -*-
"""校准工具：对 data/ 真实账单 + tests/ 合成账单，打印 v4 条件打分与 v3 原型匹配的候选，对照 expected.json。
用法: python eval/calibrate.py [--real] [--tests] [--dims]
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, ROOT)
from core import parse_bill, ParseError, apply_basic, compute_metrics, retrieve_personas
from core.retrieve import retrieve_personas_v3 as retrieve_personas_v1
from core.kb import DEFAULTS

EXP = json.load(open(os.path.join(ROOT, "tests", "expected.json"), encoding="utf-8"))


def metrics_rules(path):
    txns, rep = parse_bill(path); apply_basic(txns); return compute_metrics(txns, report=rep)


def metrics_truth(path, labels):
    txns, rep = parse_bill(path)
    for t in txns:
        c = labels.get(f"{t['time']}|{t['merchant']}|{t['amount']:.2f}")
        t["category"] = c; t["rule_id"] = None
        t["is_online"] = DEFAULTS[c]["is_online"] if c else False
        t["is_necessity"] = DEFAULTS[c]["is_necessity"] if c else False
        if c == "C8" and t["platform_category"] == "酒店旅游": t["brand_family"] = "travel"
    return compute_metrics(txns, report=rep)


def show(name, m, exp=None, dims=False):
    r3, r1 = retrieve_personas(m, tier="vip"), retrieve_personas_v1(m)
    c3 = [(c["code"], c["match"]) for c in r3["candidates"]]
    c1 = [(c["code"], c["match"]) for c in r1["candidates"]]
    flag = ""
    if exp:
        ok = c3[0][0] in exp.get("primary", [c3[0][0]]) and c3[0][0] not in exp.get("forbidden", [])
        flag = "✓" if ok else "✗"
    print(f"{flag:1} {name[:34]:34} v4 {c3}  cc={r3['close_call']} badges={[b['code'] for b in r3['badges']]} | v3 {c1}")
    if dims:
        print("     dims:", {k: v for k, v in m["dimensions"].items()}, " top5:", r3["all_matches"][:5])


if __name__ == "__main__":
    args = sys.argv[1:] or ["--real", "--tests"]
    dims = "--dims" in args
    if "--real" in args:
        D = os.path.join(ROOT, "data")
        for f in sorted(os.listdir(D)):
            if f.endswith((".csv", ".xlsx")) and not f.startswith("~$"):
                show(f.lstrip("abcdefghijklmnopqrstuvwxyz"), metrics_rules(os.path.join(D, f)), dims=dims)
    if "--tests" in args:
        n_ok = 0
        for tid, e in EXP.items():
            if e.get("parse_error"): continue
            labels = json.load(open(os.path.join(ROOT, e["labels"]), encoding="utf-8"))
            m = metrics_truth(os.path.join(ROOT, e["file"]), labels)
            show(f"{tid} exp={e.get('primary')}", m, e, dims=dims)
