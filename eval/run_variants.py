# -*- coding: utf-8 -*-
"""Stage 6 · 跑变体：20 个测试账单 × A / B / B' / C × N 轮，写 eval/results/raw/*.json 与 runs.csv（自动指标部分）。

  A   最小 LLM：脱敏原始行 + 一句话 prompt（不清洗、不算指标、无人格体系）
  B   普通版：规则分类 + 原型匹配 + M6(basic) + M7
  Bp  B'：B 的检索换成 v3 十二维原型匹配（对照 v4 条件即维度）
  C   VIP 版：规则预标注 + M3 逐笔 + 原型匹配 + M6(vip) + M7

用法: python eval/run_variants.py [--variants A,B,Bp,C] [--runs 2] [--tests T01,T06] [--no-cache]
"""
import argparse, csv, json, os, sys, time, traceback
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, ROOT)
from core import run_pipeline, llm_usage, ParseError
from core.kb import CARDS
from core.orchestrator import FORBIDDEN_WORDS, FORBIDDEN_WORDS_STRICT, ADVICE_WORDS

VARIANTS = {"A": dict(variant="A"), "B": dict(tier="basic"), "Bp": dict(tier="basic", method="v3"), "C": dict(tier="vip")}
OUT = os.path.join(ROOT, "eval", "results")
EXP = json.load(open(os.path.join(ROOT, "tests", "expected.json"), encoding="utf-8"))


def txn_key(t):
    return f"{t['time']}|{t['merchant']}|{t['amount']:.2f}"


def persona_text(r):
    p = r.get("persona") or {}
    parts = [p.get("summary", ""), p.get("one_liner", ""), p.get("keyword", "")]
    parts += [e.get("text", "") for e in (p.get("evidence") or [])]
    parts += [h.get("text", "") for h in (p.get("highlights") or [])]
    return " ".join(x for x in parts if x)


def auto_score(tid, variant, r, labels):
    """自动指标：E1（B/Bp/C）、分类准确率、E3 的规则部分、成本。"""
    exp = EXP[tid]
    out = {"E1_auto": None, "cls_acc": None, "unclassified": None, "E3_violations": [], "calls": 0, "tokens": 0,
           "fallback": False, "attempts": None, "primary": None, "primary_name": None}
    if r.get("parse_error"):
        out["E1_auto"] = 1 if exp.get("parse_error") else 0
        if not exp.get("parse_error"):
            out["E3_violations"].append("意外 ParseError")
        return out
    if exp.get("parse_error"):
        out["E1_auto"] = 0; out["E3_violations"].append("应报 ParseError 但生成了结果")
    u = llm_usage(r); out["calls"] = u["calls"]; out["tokens"] = u["prompt_tokens"] + u["completion_tokens"]
    p = r.get("persona") or {}
    text = persona_text(r)
    fw = [w for w in FORBIDDEN_WORDS + FORBIDDEN_WORDS_STRICT if w in text]
    if fw: out["E3_violations"].append(f"禁词 {fw}")
    aw = [w for w in ADVICE_WORDS if w in text]
    if aw: out["E3_violations"].append(f"建议用语 {aw}")
    if variant == "A":
        out["primary_name"] = p.get("persona_name")
        return out                                     # E1 由 judge 判断
    code = p.get("primary_persona"); out["primary"] = code; out["primary_name"] = CARDS.get(code, {}).get("name")
    exp_primary = exp.get("primary_basic", exp.get("primary")) if variant in ("B", "Bp") else exp.get("primary")
    ok = True
    if exp_primary and code not in exp_primary:
        ok = False
        if exp.get("co_display"):                          # 并列人格用例：预期卡出现在前两位候选或被选为副人格即算对
            top2 = [c["code"] for c in (r.get("retrieval") or {}).get("candidates", [])[:2]]
            ok = bool(set(exp_primary) & set(top2 + [p.get("secondary_persona")]))
    if code in exp.get("forbidden", []): ok = False; out["E3_violations"].append(f"命中禁止人格 {code}")
    out["E1_auto"] = 1 if ok else 0
    cands = [c["code"] for c in (r.get("retrieval") or {}).get("candidates", [])]
    if cands and code not in cands: out["E3_violations"].append("主人格不在候选内")
    if exp.get("data_level") and r["metrics"]["data_level"] != exp["data_level"]:
        out["E3_violations"].append(f"data_level {r['metrics']['data_level']} ≠ {exp['data_level']}")
    for k, v in exp.get("report", {}).items():
        if r["report"].get(k, 0) != v: out["E3_violations"].append(f"report.{k}={r['report'].get(k, 0)}≠{v}")
    if exp.get("confidence") and p.get("confidence") and p["confidence"] == "high" and exp["confidence"] != "high":
        out["E3_violations"].append(f"confidence 应为 {exp['confidence']}")
    rv = r.get("review") or {}
    out["fallback"] = bool(rv.get("fallback")); out["attempts"] = rv.get("attempts")
    txns = r.get("txns") or []
    if txns:
        hit = sum(t.get("category") == labels.get(txn_key(t)) for t in txns)
        out["cls_acc"] = round(hit / len(txns), 3)
        out["unclassified"] = round(sum(t.get("category") is None for t in txns) / len(txns), 3)
    return out


def slim(r):
    """落盘时去掉大字段（交易全文、prompt 全文），保留评估需要的。"""
    s = {k: v for k, v in r.items() if k not in ("txns", "llm_calls", "metrics", "retrieval")}
    s["txns"] = [{"key": txn_key(t), "category": t.get("category"), "source": t.get("source_of_label"),
                  "confidence": t.get("confidence")} for t in r.get("txns") or []]
    m = r.get("metrics") or {}
    s["metrics"] = {k: m.get(k) for k in ("total", "txn_count", "data_level", "category_share", "category_amount", "dimensions",
                                          "unclassified_ratio", "top_category", "top_merchants", "outliers", "highlights_candidates",
                                          "impulse_share", "meal_slot_dist", "scene_dist", "late_meal_ratio", "after_work_share",
                                          "food_share", "delivery_ratio", "online_share", "shopping_share", "small_txn_ratio",
                                          "big_ticket_share", "late_night_ratio", "commute_count_ratio", "necessity_share",
                                          "game_share", "travel_share", "median_amount", "txn_per_day", "beverage_per_week",
                                          "category_count", "active_days") if k in m}
    ret = r.get("retrieval") or {}
    s["retrieval"] = {"candidates": ret.get("candidates"), "close_call": ret.get("close_call"), "special": ret.get("special"),
                      "modifier_tags": ret.get("modifier_tags")}
    s["llm_calls"] = [{k: v for k, v in c.items() if k not in ("system", "user")} for c in r.get("llm_calls") or []]
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variants", default="A,B,Bp,C"); ap.add_argument("--runs", type=int, default=2)
    ap.add_argument("--tests", default=""); ap.add_argument("--collect", action="store_true")
    a = ap.parse_args()
    if a.collect:
        collect(); return
    os.makedirs(os.path.join(OUT, "raw"), exist_ok=True)
    tests = a.tests.split(",") if a.tests else list(EXP)
    rows = []
    for tid in tests:
        exp = EXP[tid]; path = os.path.join(ROOT, exp["file"])
        labels = json.load(open(os.path.join(ROOT, exp["labels"]), encoding="utf-8")) if os.path.exists(os.path.join(ROOT, exp["labels"])) else {}
        for v in a.variants.split(","):
            for run in range(1, a.runs + 1):
                t0 = time.time(); rid = f"{tid}_{v}_r{run}"
                try:
                    r = run_pipeline(path, salt=f"run{run}", **VARIANTS[v])
                except ParseError as e:
                    r = {"parse_error": str(e), "persona": None}
                except Exception as e:
                    r = {"parse_error": None, "error": f"{type(e).__name__}: {e}", "persona": None, "trace": traceback.format_exc()[-800:]}
                sc = auto_score(tid, v, r, labels) if "error" not in r else {"E1_auto": 0, "E3_violations": [f"crash {r['error']}"], "calls": 0, "tokens": 0}
                rec = {"id": rid, "test": tid, "variant": v, "run": run, "group": exp["group"], "elapsed": round(time.time() - t0, 1), **sc}
                rows.append(rec)
                json.dump({"meta": rec, "result": slim(r) if "persona" in r and r.get("persona") is not None else r},
                          open(os.path.join(OUT, "raw", rid + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                print(f"{rid:14} E1={sc.get('E1_auto')} primary={sc.get('primary') or sc.get('primary_name')} "
                      f"acc={sc.get('cls_acc')} calls={sc.get('calls')} tok={sc.get('tokens')} viol={sc.get('E3_violations')} {rec['elapsed']}s", flush=True)
    collect()


def collect():
    """从 raw/*.json 的 meta 重建 runs.csv（多个进程并行跑时各自落盘，最后统一汇总）。"""
    rows = []
    for f in sorted(os.listdir(os.path.join(OUT, "raw"))):
        if f.endswith(".json"):
            rows.append(json.load(open(os.path.join(OUT, "raw", f), encoding="utf-8"))["meta"])
    order = {"A": 0, "B": 1, "Bp": 2, "C": 3}
    rows.sort(key=lambda r: (r["test"], order.get(r["variant"], 9), r["run"]))
    keys = ["id", "test", "variant", "run", "group", "E1_auto", "primary", "primary_name", "cls_acc", "unclassified",
            "E3_violations", "calls", "tokens", "fallback", "attempts", "elapsed"]
    with open(os.path.join(OUT, "runs.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore"); w.writeheader()
        for r in rows:
            r = dict(r); r["E3_violations"] = "; ".join(r.get("E3_violations") or []); w.writerow(r)
    print("wrote", os.path.join(OUT, "runs.csv"), len(rows), "rows")


if __name__ == "__main__":
    main()
