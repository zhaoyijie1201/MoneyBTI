# -*- coding: utf-8 -*-
"""知识库加载：rag/personas.json 与 rag/merchant_rules.json 是唯一知识来源。"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.normpath(os.path.join(HERE, ".."))
RAG_DIR = os.path.join(PROJECT_DIR, "rag")


def _load(name):
    with open(os.path.join(RAG_DIR, name), encoding="utf-8") as f:
        return json.load(f)


RULES = _load("merchant_rules.json")
PERSONAS = _load("personas.json")
DEFAULTS = RULES["_meta"]["category_defaults"]
CATEGORIES = RULES["_meta"]["categories"]          # {"C1": "外卖", ...}
CARDS = {c["code"]: c for c in PERSONAS["cards"]}   # code -> card
MODIFIER_TAGS = PERSONAS["modifier_tags"]


def card(code):
    return CARDS[code]


def card_for_prompt(code):
    """送入 LLM 的人格卡：去掉 illustration_prompt。"""
    c = dict(CARDS[code])
    c.pop("illustration_prompt", None)
    return c
