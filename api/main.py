# -*- coding: utf-8 -*-
"""MoneyBTI 钱格 · FastAPI 后端（Stage 5 原型）。

接口与 UI 面板一一对应：
  POST /api/upload    (file, tier)          面板 ①  M1 解析 + D0 + M2 [+ M3]      → session_id, txns, report
  POST /api/demo      {sample, tier}        面板 ①  用 tests/bills 里的合成账单代替上传
  POST /api/confirm   {session_id, overrides, method}  面板 ②→③  M4 + M5 + M2'  → metrics, dimensions, candidates
  POST /api/generate  {session_id, regenerate}         面板 ④  M6 + 审查 + M7   → persona, copy, review, llm_calls
  GET  /api/personas                                   人格图鉴 + 维度定义
  GET  /api/samples                                    可用的演示账单
静态页在 web/，同源托管。上传文件解析后立即删除，session 只留在内存。
"""
import os, sys, time, uuid, tempfile, json
from typing import Optional, Dict

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, ROOT)

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core import stage_classify, stage_metrics, stage_generate, ParseError, PERSONAS, CATEGORIES, public_txn
from core.llm import LLMError

app = FastAPI(title="MoneyBTI 钱格 API", version="4.0")
SESSIONS: Dict[str, dict] = {}
SESSION_TTL = 3600
SAMPLES_DIR = os.path.join(ROOT, "tests", "bills")
EXPECTED = json.load(open(os.path.join(ROOT, "tests", "expected.json"), encoding="utf-8")) if os.path.exists(os.path.join(ROOT, "tests", "expected.json")) else {}


def _gc():
    now = time.time()
    for k in [k for k, v in SESSIONS.items() if now - v["created"] > SESSION_TTL]:
        SESSIONS.pop(k, None)


def _session(sid):
    s = SESSIONS.get(sid)
    if not s:
        raise HTTPException(404, "session 不存在或已过期，请重新上传")
    return s


def _classify_view(s):
    return {"session_id": s["id"], "tier": s["tier"], "report": s["report"], "layers": s["layers"], "m3": s["m3"],
            "decisions": s["decisions"], "txns": [public_txn(t) for t in s["txns"]],
            "stats": {"total_rows": len(s["txns"]),
                      "rule_rows": sum(1 for t in s["txns"] if (t.get("source_of_label") or "").startswith("rule")),
                      "llm_rows": sum(1 for t in s["txns"] if t.get("source_of_label") == "llm"),
                      "unclassified": sum(1 for t in s["txns"] if not t.get("category")),
                      "low_confidence": sum(1 for t in s["txns"] if t.get("confidence", 1) < 0.5),
                      "ambiguous": sum(1 for t in s["txns"] if t.get("ambiguous"))}}


def _start(path, tier):
    _gc()
    try:
        c = stage_classify(path, tier=tier, use_llm=True, salt="")
    except ParseError as e:
        raise HTTPException(400, f"账单无法解析：{e}")
    except LLMError as e:
        raise HTTPException(502, f"LLM 调用失败：{e}")
    sid = uuid.uuid4().hex[:12]
    s = {"id": sid, "tier": tier, "created": time.time(), "txns": c["txns"], "report": c["report"], "layers": c["layers"],
         "m3": c["m3"], "decisions": c["decisions"], "log": c["log"], "regen": 0}
    SESSIONS[sid] = s
    return _classify_view(s)


@app.post("/api/upload")
async def upload(file: UploadFile = File(...), tier: str = Form("basic")):
    if tier not in ("basic", "vip"):
        raise HTTPException(400, "tier 必须是 basic 或 vip")
    suffix = ".xlsx" if file.filename.lower().endswith(".xlsx") else ".csv"
    data = await file.read()
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(413, "文件超过 5 MB")
    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        return _start(path, tier)
    finally:
        try:
            os.remove(path)          # 原始文件解析后立即删除
        except OSError:
            pass


class DemoReq(BaseModel):
    sample: str = "T06"
    tier: str = "basic"


@app.post("/api/demo")
def demo(req: DemoReq):
    files = [f for f in os.listdir(SAMPLES_DIR) if f.startswith(req.sample + ".")]
    if not files:
        raise HTTPException(404, "没有这个演示账单")
    return _start(os.path.join(SAMPLES_DIR, files[0]), req.tier)


class ConfirmReq(BaseModel):
    session_id: str
    overrides: Optional[Dict[str, str]] = None
    method: str = "v4"


@app.post("/api/confirm")
def confirm(req: ConfirmReq):
    s = _session(req.session_id)
    m = stage_metrics(s["txns"], s["report"], tier=s["tier"], user_overrides=req.overrides or None,
                      method=req.method, decisions=s["decisions"])
    s.update(metrics=m["metrics"], retrieval=m["retrieval"], warnings=m["warnings"], method=req.method)
    s.pop("persona", None)
    return {"session_id": s["id"], "tier": s["tier"], "metrics": m["metrics"], "retrieval": m["retrieval"],
            "warnings": m["warnings"], "decisions": s["decisions"], "txns": [public_txn(t) for t in s["txns"]]}


class GenReq(BaseModel):
    session_id: str
    regenerate: bool = False
    lang: str = "zh"


@app.post("/api/generate")
def generate(req: GenReq):
    s = _session(req.session_id)
    if "metrics" not in s:
        raise HTTPException(400, "请先调用 /api/confirm")
    if req.regenerate:
        s["regen"] += 1
    salt = f"regen{s['regen']}" if s["regen"] else ""
    lang = "en" if req.lang == "en" else "zh"
    try:
        g = stage_generate(s["tier"], s["metrics"], s["retrieval"], use_llm=True, salt=salt, decisions=s["decisions"], log=s["log"], lang=lang)
    except LLMError as e:
        raise HTTPException(502, f"LLM 调用失败：{e}")
    s.update(persona=g["persona"], copy=g["copy"], review=g["review"])
    calls = [{k: v for k, v in c.items()} for c in s["log"]]
    return {"session_id": s["id"], "tier": s["tier"], "lang": lang, "persona": g["persona"], "copy": g["copy"], "review": g["review"],
            "decisions": s["decisions"], "llm_calls": calls, "metrics": s["metrics"], "retrieval": s["retrieval"],
            "report": s["report"], "warnings": s.get("warnings", [])}


@app.get("/api/personas")
def personas():
    cards = [{k: v for k, v in c.items() if k != "illustration_prompt"} for c in PERSONAS["cards"]]
    return {"cards": cards, "dimensions": PERSONAS["dimensions"], "modifier_tags": PERSONAS["modifier_tags"], "badges": PERSONAS.get("badges", []), "categories": CATEGORIES}


@app.get("/api/samples")
def samples():
    out = []
    for f in sorted(os.listdir(SAMPLES_DIR)):
        tid = f.split(".")[0]
        e = EXPECTED.get(tid, {})
        out.append({"id": tid, "file": f, "group": e.get("group"), "note": e.get("note"), "expected": e.get("primary")})
    return out


@app.get("/api/health")
def health():
    return {"ok": True, "sessions": len(SESSIONS)}


WEB = os.path.join(ROOT, "web")


@app.get("/")
def index():
    return FileResponse(os.path.join(WEB, "index.html"))


@app.middleware("http")
async def no_cache_static(request, call_next):
    resp = await call_next(request)
    if not request.url.path.startswith("/api/") and not request.url.path.startswith("/cats/"):
        resp.headers["Cache-Control"] = "no-cache, must-revalidate"   # 浏览器每次校验 ETag，避免改版后看到旧页面
    return resp


app.mount("/", StaticFiles(directory=WEB), name="web")
