# -*- coding: utf-8 -*-
"""不含 LLM 的确定性流水线：M1 → M2 → M5 → M2'。
普通版到这里为止只差 M6 / M7（第 3 步 orchestrator 接入）；评估脚本与 API 都从这里取数。
"""
from .parser import parse_bill
from .classify import apply_basic, apply_user_labels
from .metrics import compute_metrics
from .retrieve import retrieve_personas


def analyze_rules(path, user_overrides=None, tier="basic"):
    """返回 dict(txns, report, layers, metrics, retrieval)。txns 含 dt 对象，序列化前用 public_txn()。"""
    txns, report = parse_bill(path)
    layers = apply_basic(txns)
    if user_overrides:
        apply_user_labels(txns, user_overrides)
    metrics = compute_metrics(txns, report=report)
    retrieval = retrieve_personas(metrics, tier=tier)
    return {"txns": txns, "report": report, "layers": layers, "metrics": metrics, "retrieval": retrieval}


def public_txn(t):
    """给 UI / API 的交易行（不含 dt 对象）。姓名、账号、订单号在 parser 阶段就没有读入。"""
    return {k: v for k, v in t.items() if k != "dt"}
