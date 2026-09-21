# -*- coding: utf-8 -*-
"""M1 Parser：支付宝 CSV / xlsx 与微信 xlsx / CSV → 统一 Transaction 列表 + 数据质量报告。
实现设计文档 3.1–3.4 节（R1–R8）。不调用 LLM；姓名 / 账号 / 订单号 / 支付方式不出本函数。
"""
import csv, io, re
from collections import Counter
from datetime import datetime

_TIME_FORMATS = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M",
                 "%Y-%m-%d", "%Y/%m/%d")
_DISCOUNT_KEYS = ("优惠", "立减", "红包", "券", "积分")
_AMBIGUOUS_KEYS = ("押金", "学费", "房租", "收钱码收款")


class ParseError(ValueError):
    """文件无法识别为支付宝 / 微信账单（T15：空文件、只有表头、格式不对）。"""


def _decode(raw: bytes) -> str:
    for enc in ("utf-8-sig", "gbk", "gb18030"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    raise ParseError("无法识别文件编码")


def _parse_time(s):
    """支付宝原始为 2026-07-28 14:05:14；Excel 另存后可能变成 2026/5/31 17:44。"""
    s = str(s).strip()[:19]
    for f in _TIME_FORMATS:
        try:
            return datetime.strptime(s, f)
        except ValueError:
            continue
    return None


def _rows_from_lines(lines):
    try:
        hdr = next(i for i, l in enumerate(lines) if l.lstrip().startswith("交易时间"))
    except StopIteration:
        raise ParseError("找不到以「交易时间」开头的表头行，不是支付宝 / 微信账单")
    rows = list(csv.reader(io.StringIO("\n".join(lines[hdr:]))))
    cols = [c.strip() for c in rows[0]]
    return [dict(zip(cols, [x.strip() for x in r])) for r in rows[1:] if len(r) >= 9]


def _rows_from_xlsx(path):
    import pandas as pd
    df = pd.read_excel(path, header=None)
    if df.shape[1] == 1:
        # 用 Excel 直接打开 CSV 再另存：每个单元格是一整行 CSV 文本
        return _rows_from_lines([str(v) for v in df.iloc[:, 0].tolist() if str(v) != "nan"])
    try:
        hdr = next(i for i in range(min(40, len(df))) if str(df.iloc[i, 0]).startswith("交易时间"))
    except StopIteration:
        raise ParseError("找不到以「交易时间」开头的表头行，不是支付宝 / 微信账单")
    cols = [str(c).strip() for c in df.iloc[hdr]]
    out = []
    for _, r in df.iloc[hdr + 1:].iterrows():
        out.append({c: ("" if str(v) == "nan" else str(v).strip()) for c, v in zip(cols, r)})
    return out


def _header_text(path, raw=None):
    if path.lower().endswith(".xlsx"):
        import pandas as pd
        df = pd.read_excel(path, header=None, nrows=40)
        return "\n".join(str(v) for v in df.iloc[:, 0].tolist())
    return _decode(raw if raw is not None else open(path, "rb").read())[:4000]


def _period_from_header(text):
    """支付宝 / 微信头部都有 起始时间：[YYYY-MM-DD ...] 终止时间：[YYYY-MM-DD ...]。取不到返回 (None, None)。"""
    m1 = re.search(r"起始时间[：:]\s*\[?(\d{4}[-/]\d{1,2}[-/]\d{1,2})", text)
    m2 = re.search(r"终止时间[：:]\s*\[?(\d{4}[-/]\d{1,2}[-/]\d{1,2})", text)
    if m1 and m2:
        d1, d2 = (datetime.strptime(m.group(1).replace("/", "-"), "%Y-%m-%d").date() for m in (m1, m2))
        return d1, d2
    return None, None


def parse_bill(path):
    """返回 (统一 Transaction 列表, 质量报告)。

    Transaction 字段：id, time(ISO str), dt, hour, weekday, source, platform_category, merchant, description,
    amount, ttype, masked, ambiguous, outlier, discount, is_late_night。
    报告字段：raw, valid, R1_not_expense, R2_refund_closed, R3_zero, R4_transfer, bad_amount, bad_time,
    source, period_start, period_end, period_days, period_from_header。
    """
    if path.lower().endswith(".xlsx"):
        raw_rows = _rows_from_xlsx(path)
        header = _header_text(path)
    else:
        raw = open(path, "rb").read()
        raw_rows = _rows_from_lines(_decode(raw).splitlines())
        header = _header_text(path, raw)
    if not raw_rows:
        raise ParseError("账单里没有交易行（空文件或只有表头）")
    is_wechat = "交易类型" in raw_rows[0]
    report = Counter(raw=len(raw_rows))
    txns = []
    for r in raw_rows:
        if is_wechat:
            t = dict(time=r.get("交易时间", ""), platform_category="", merchant=r.get("交易对方", ""),
                     description=r.get("商品", ""), amount=r.get("金额(元)", ""), flow=r.get("收/支", ""),
                     status=r.get("当前状态", ""), ttype=r.get("交易类型", ""), source="wechat",
                     pay_method=r.get("支付方式", ""))
        else:
            t = dict(time=r.get("交易时间", ""), platform_category=r.get("交易分类", ""), merchant=r.get("交易对方", ""),
                     description=r.get("商品说明", ""), amount=r.get("金额", ""), flow=r.get("收/支", ""),
                     status=r.get("交易状态", ""), ttype="", source="alipay",
                     pay_method=r.get("收/付款方式", ""))
        # 支付方式只在本机用于「薅羊毛」指标，不进入 LLM 输入
        t["discount"] = any(k in t["pay_method"] for k in _DISCOUNT_KEYS)
        del t["pay_method"]
        try:
            t["amount"] = float(str(t["amount"]).replace("¥", "").replace(",", ""))
        except ValueError:
            report["bad_amount"] += 1; continue
        if t["flow"] != "支出":
            report["R1_not_expense"] += 1; continue
        if t["status"] in ("交易关闭", "已全额退款", "退款成功") or "退款" in t["ttype"]:
            report["R2_refund_closed"] += 1; continue
        if t["amount"] <= 0:
            report["R3_zero"] += 1; continue
        if (t["platform_category"] == "转账红包" or t["ttype"] in ("转账", "微信红包（单发）")
                or any(k in t["description"] for k in ("转账", "红包"))):
            report["R4_transfer"] += 1; continue
        t["masked"] = bool(re.search(r"\*{2,}", t["merchant"]))                                   # R5
        t["ambiguous"] = t["ttype"] == "扫二维码付款" or any(k in t["description"] for k in _AMBIGUOUS_KEYS)  # R8
        dt = _parse_time(t["time"])
        if dt is None:
            report["bad_time"] += 1; continue
        t["time"] = dt.strftime("%Y-%m-%dT%H:%M:%S")
        t["dt"], t["hour"], t["weekday"] = dt, dt.hour, dt.weekday()
        t["is_late_night"] = dt.hour >= 21 or dt.hour < 5     # v4：21:00–04:59
        del t["flow"], t["status"]
        txns.append(t)
    txns.sort(key=lambda t: t["dt"])
    total = sum(t["amount"] for t in txns)
    for i, t in enumerate(txns, 1):
        t["id"] = f"t{i:03d}"
        t["outlier"] = total > 0 and t["amount"] >= 0.30 * total                                  # R7
    report["valid"] = len(txns)
    report["source"] = "wechat" if is_wechat else "alipay"
    start, end = _period_from_header(header)
    report["period_from_header"] = start is not None
    if start is None and txns:
        start, end = txns[0]["dt"].date(), txns[-1]["dt"].date()
    report["period_start"] = start.isoformat() if start else None
    report["period_end"] = end.isoformat() if end else None
    report["period_days"] = (end - start).days + 1 if start else None
    return txns, dict(report)


def raw_rows(path, max_desc=40):
    """变体 A 用：不做 R1–R8 清洗，所有行（含收入 / 退款 / 转账 / 关闭）都给 LLM，只脱敏。"""
    if path.lower().endswith(".xlsx"):
        rows = _rows_from_xlsx(path)
    else:
        rows = _rows_from_lines(_decode(open(path, "rb").read()).splitlines())
    if not rows:
        raise ParseError("账单里没有交易行（空文件或只有表头）")
    is_wechat = "交易类型" in rows[0]
    out = []
    for r in rows:
        if is_wechat:
            out.append(f"{r.get('交易时间','')} | {r.get('交易类型','')} | {r.get('交易对方','')} | {r.get('商品','')[:max_desc]} | "
                       f"{r.get('收/支','')} | {r.get('金额(元)','')} | {r.get('当前状态','')}")
        else:
            out.append(f"{r.get('交易时间','')} | {r.get('交易分类','')} | {r.get('交易对方','')} | {r.get('商品说明','')[:max_desc]} | "
                       f"{r.get('收/支','')} | {r.get('金额','')} | {r.get('交易状态','')}")
    return out


def to_llm_row(t, max_desc=40):
    """3.3 节：送入 LLM 的字段仅限 time、weekday、platform_category、merchant、description(截 40 字)、amount，
    外加 is_late_night 与规则预标注 rule_label。"""
    return {"id": t["id"], "time": t["time"][:16], "weekday": t["dt"].strftime("%a"),
            "platform_category": t["platform_category"], "merchant": t["merchant"],
            "description": t["description"][:max_desc], "amount": t["amount"],
            "is_late_night": t["is_late_night"], "rule_label": t.get("category")}
