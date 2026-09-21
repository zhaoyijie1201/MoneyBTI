# -*- coding: utf-8 -*-
"""一次性把人格知识库翻成英文，落盘到 rag/personas_en.json（build_personas_v4.py 重建时自动合并为 *_en 字段）。

翻译对象：每张卡的 traits / 条件 label / tone / axis / core_categories / do_not_say / guardrails / distinguish；徽章 name / line；
名称用设计稿英文名（web/ticket-copy.js），解读与一句话概括文档里已有英文，缺的（精致主义者）补译。
运行: python eval/translate_kb.py  （已翻过的卡跳过；--force 全部重翻）
"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, ROOT)
from core.llm import call_json

KB = os.path.join(ROOT, "rag", "personas.json")
OUT = os.path.join(ROOT, "rag", "personas_en.json")
SYSTEM = """You translate a Chinese product knowledge base for a spending-personality app into natural, concise English.
Keep the playful, non-judgemental tone. Keep every list the same length and order as the input. Keep numbers, ≥ / ≤ symbols,
percentages and currency (¥) unchanged. Category codes like C1 stay as they are. Persona names are given — do not change them.
Output ONLY a JSON object with exactly the same keys as the input, values translated."""


def cond_labels(card):
    if card.get("mode") == "count":
        return [c["label"] for c in card["conditions"]]
    return [c["label"] for g in card.get("rule_groups", []) for c in g]


def main():
    force = "--force" in sys.argv
    kb = json.load(open(KB, encoding="utf-8"))
    copy_js = open(os.path.join(ROOT, "web", "ticket-copy.js"), encoding="utf-8").read()
    copy = json.loads(copy_js.split("=", 1)[1].rstrip().rstrip(";"))
    out = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) and not force else {"cards": {}, "badges": {}}
    for card in kb["cards"]:
        code = card["code"]
        if code in out["cards"] and not force:
            continue
        payload = {"name": copy.get(code, {}).get("englishName", card["name"]), "axis": card.get("axis", ""),
                   "traits": card.get("traits", []), "condition_labels": cond_labels(card), "tone": card.get("tone", ""),
                   "core_categories": card.get("core_categories", ""), "do_not_say": card.get("do_not_say", []),
                   "guardrails": card.get("guardrails", []), "distinguish": card.get("distinguish", []), "focus": card.get("focus", "")}
        if not card.get("interpretation_en"):
            payload["interpretation"] = card.get("interpretation", "")
        if not card.get("tagline_en"):
            payload["tagline"] = card.get("tagline", "")
        obj, meta = call_json(SYSTEM, "Translate: " + json.dumps(payload, ensure_ascii=False), temperature=0.1, max_tokens=2500, module="M6")
        ok = all(len(obj.get(k, [])) == len(v) for k, v in payload.items() if isinstance(v, list))
        if not ok:
            print("length mismatch, retrying", code)
            obj, meta = call_json(SYSTEM, "Translate (keep list lengths!): " + json.dumps(payload, ensure_ascii=False), temperature=0.1, max_tokens=2500, module="M6", salt="retry")
        obj["name"] = payload["name"]
        out["cards"][code] = obj
        print(code, obj["name"], "|", obj.get("traits"), "|", (obj.get("condition_labels") or [""])[0])
    for b in kb.get("badges", []):
        if b["code"] in out["badges"] and not force:
            continue
        obj, _ = call_json(SYSTEM, "Translate: " + json.dumps({"name": b["name"], "line": b.get("line", "")}, ensure_ascii=False), temperature=0.1, max_tokens=300, module="M6")
        out["badges"][b["code"]] = obj
        print("badge", b["code"], obj)
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("saved", OUT)


if __name__ == "__main__":
    main()
