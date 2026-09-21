# -*- coding: utf-8 -*-
"""MoneyBTI 钱格 · 核心逻辑（唯一实现，评估脚本与 API 共用）。

  parser.parse_bill      M1 解析清洗
  classify.apply_basic   M2 普通版三层规则分类
  metrics.compute_metrics M5 指标
  retrieve.retrieve_personas M2' 人格卡检索
  pipeline.analyze_rules 以上四步串起来
"""
from .parser import parse_bill, ParseError, to_llm_row
from .classify import classify_basic, apply_basic, apply_user_labels
from .metrics import compute_metrics
from .retrieve import retrieve_personas, retrieve_personas_v3, card_match, cond_score, badges_for
from .pipeline import analyze_rules, public_txn
from .kb import RULES, PERSONAS, CARDS, CATEGORIES, DEFAULTS
from .orchestrator import run_pipeline, llm_usage, stage_classify, stage_metrics, stage_generate

__all__ = ["parse_bill", "ParseError", "to_llm_row", "classify_basic", "apply_basic", "apply_user_labels",
           "compute_metrics", "retrieve_personas", "retrieve_personas_v3", "card_match", "cond_score", "badges_for", "analyze_rules",
           "public_txn", "run_pipeline", "llm_usage", "stage_classify", "stage_metrics", "stage_generate", "RULES", "PERSONAS", "CARDS", "CATEGORIES", "DEFAULTS"]
