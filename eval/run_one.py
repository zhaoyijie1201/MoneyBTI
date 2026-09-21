# -*- coding: utf-8 -*-
"""单账单跑通整条流水线，打印人格结果与决策日志。用法: python eval/run_one.py tests/bills/T06.csv [basic|vip|A]"""
import json, os, sys
sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))
from core import run_pipeline, llm_usage

path = sys.argv[1]
mode = sys.argv[2] if len(sys.argv) > 2 else "basic"
lang = "en" if "en" in sys.argv[3:] else "zh"
r = run_pipeline(path, tier="vip" if mode == "vip" else "basic", variant="A" if mode == "A" else None, lang=lang)
print("== persona ==");  print(json.dumps(r["persona"], ensure_ascii=False, indent=1))
print("== copy ==", json.dumps(r.get("copy"), ensure_ascii=False))
print("== review ==", json.dumps(r.get("review"), ensure_ascii=False))
if r.get("m3"): print("== m3 ==", {k: (v if not isinstance(v, list) else len(v)) for k, v in r["m3"].items()})
for d in r.get("decisions", []): print("  ", d)
print("== usage ==", llm_usage(r))
for c in r["llm_calls"]:
    if "error" in c: print("  !! ", c["module"], c["error"])
