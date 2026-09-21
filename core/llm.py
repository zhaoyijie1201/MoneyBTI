# -*- coding: utf-8 -*-
"""LLM 客户端（OpenAI 兼容 chat.completions），支持两个提供商与按模块选模型。

  提供商  MONEYBTI_PROVIDER = openrouter（默认）| bailian
    openrouter  base_url https://openrouter.ai/api/v1，key 来自 OPENROUTER_API_KEY 或根目录 open_router_api_key.txt / OpenRouter_api.txt
    bailian     阿里云百炼兼容接口，key 来自 DASHSCOPE_API_KEY 或根目录 api_key.txt，extra_body enable_thinking=false
  模型    MONEYBTI_MODEL（缺省）、MONEYBTI_MODEL_M3 / _M6 / _M7 / _JUDGE 按模块覆盖
  缓存    所有调用按 (model, messages, temperature, …) 哈希缓存到 cache/，换模型自动失效
  JSON    call_json() 只接受合法 JSON，解析失败自动重试一次（M0 决策点 D3 的底层实现）
"""
import hashlib, json, os, re, time

from .kb import PROJECT_DIR

PROVIDER = os.environ.get("MONEYBTI_PROVIDER", "openrouter").lower()
PROVIDERS = {
    "openrouter": {"base_url": "https://openrouter.ai/api/v1", "env_key": "OPENROUTER_API_KEY",
                   "key_files": ["open_router_api_key.txt", "OpenRouter_api.txt"],
                   "default_model": "deepseek/deepseek-v4-flash",
                   "default_models": {"M3": "deepseek/deepseek-v4-flash", "M6": "deepseek/deepseek-v4-flash",
                                      "M7": "deepseek/deepseek-v4-flash", "JUDGE": "google/gemini-2.5-flash"}},
    "bailian": {"base_url": "https://ws-7dk30ng1m821a5jn.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
                "env_key": "DASHSCOPE_API_KEY", "key_files": ["api_key.txt"],
                "default_model": "qwen3.8-max", "default_models": {}},
}
CFG = PROVIDERS.get(PROVIDER, PROVIDERS["openrouter"])
BASE_URL = os.environ.get("MONEYBTI_BASE_URL", CFG["base_url"])
MODEL = os.environ.get("MONEYBTI_MODEL", CFG["default_model"])
CACHE_DIR = os.path.join(PROJECT_DIR, "cache")
DEFAULT_TEMPERATURE = 0.3


class LLMError(RuntimeError):
    pass


def model_for(module=None):
    """按模块取模型：环境变量 MONEYBTI_MODEL_<模块> > 提供商默认表 > MONEYBTI_MODEL。"""
    if module:
        env = os.environ.get(f"MONEYBTI_MODEL_{module.upper()}")
        if env:
            return env
        if os.environ.get("MONEYBTI_MODEL"):
            return os.environ["MONEYBTI_MODEL"]
        return CFG["default_models"].get(module.upper(), MODEL)
    return MODEL


def _api_key():
    k = os.environ.get(CFG["env_key"])
    if k:
        return k.strip()
    for name in CFG["key_files"]:
        p = os.path.join(PROJECT_DIR, name)
        if os.path.exists(p):
            return open(p, encoding="utf-8").read().strip()
    raise LLMError(f"没有找到 API key：设置 {CFG['env_key']} 或在项目根目录放 {CFG['key_files'][0]}")


_client = None


def client():
    global _client
    if _client is None:
        from openai import OpenAI
        headers = {"HTTP-Referer": "https://github.com/moneybti", "X-Title": "MoneyBTI"} if PROVIDER == "openrouter" else None
        _client = OpenAI(api_key=_api_key(), base_url=BASE_URL, default_headers=headers)
    return _client


def _extra_body(thinking):
    if PROVIDER == "bailian":
        return {"enable_thinking": thinking}
    # OpenRouter：统一关闭推理模式（分类 / 文案任务不需要，且省 token）；需要时 thinking=True
    return {"reasoning": {"enabled": bool(thinking)}} if not thinking else {}


def _cache_key(model, messages, temperature, thinking, json_mode, salt):
    h = hashlib.sha256(json.dumps([model, messages, temperature, thinking, json_mode, salt],
                                  ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    return h[:24]


def extract_json(text):
    """去掉 ```json 围栏，取第一个 { 或 [ 到最后一个 } 或 ] 之间的内容。"""
    t = text.strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t, flags=re.S)
    m = re.search(r"[\[{]", t)
    if not m:
        raise ValueError("no JSON start")
    end = max(t.rfind("}"), t.rfind("]"))
    return json.loads(t[m.start():end + 1])


def chat(system, user, temperature=DEFAULT_TEMPERATURE, thinking=False, json_mode=True, use_cache=True,
         salt="", max_tokens=4000, model=None, module=None):
    """返回 dict(text, cached, prompt_tokens, completion_tokens, latency, model)。"""
    model = model or model_for(module)
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    key = _cache_key(model, messages, temperature, thinking, json_mode, salt)
    path = os.path.join(CACHE_DIR, key + ".json")
    if use_cache and os.path.exists(path):
        d = json.load(open(path, encoding="utf-8"))
        d["cached"] = True
        return d
    kwargs = dict(model=model, messages=messages, temperature=temperature, max_tokens=max_tokens)
    eb = _extra_body(thinking)
    if eb:
        kwargs["extra_body"] = eb
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    t0 = time.time()
    try:
        r = client().chat.completions.create(**kwargs)
    except Exception as e:
        raise LLMError(f"{type(e).__name__}: {str(e)[:300]}") from e
    if not r.choices:
        raise LLMError(f"模型 {model} 没有返回 choices：{getattr(r, 'error', None) or r}")
    d = {"text": r.choices[0].message.content or "", "cached": False, "model": model,
         "prompt_tokens": getattr(r.usage, "prompt_tokens", 0) or 0, "completion_tokens": getattr(r.usage, "completion_tokens", 0) or 0,
         "latency": round(time.time() - t0, 2), "temperature": temperature}
    if use_cache:
        os.makedirs(CACHE_DIR, exist_ok=True)
        json.dump(d, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return d


def call_json(system, user, retries=1, **kw):
    """调用并解析 JSON；解析失败带同样 prompt 重试（换 salt 绕过缓存）。返回 (obj, meta)。"""
    last = None
    base_salt = kw.pop("salt", "")
    for i in range(retries + 1):
        d = chat(system, user, salt=base_salt + (f"retry{i}" if i else ""), **kw)
        try:
            return extract_json(d["text"]), d
        except (ValueError, json.JSONDecodeError) as e:
            last = (e, d)
    e, d = last
    raise LLMError(f"LLM 输出不是合法 JSON（已重试 {retries} 次）: {d['text'][:120]!r}")
