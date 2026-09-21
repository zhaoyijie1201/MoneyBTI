---
title: MoneyBTI 钱格
emoji: 🐱
colorFrom: yellow
colorTo: red
sdk: docker
app_port: 7860
pinned: false
---

# MoneyBTI 钱格

上传支付宝 / 微信月账单，代码算指标与 11/12 维消费维度，规则匹配 23 张人格原型，AI 只在候选内选择并写文案，输出带匹配度与雷达的花钱人格 + 可分享小票。PE6203 Generative AI & Agentic AI 小组作业原型。

## 本地运行

```
pip install -r requirements.txt
set OPENROUTER_API_KEY=sk-or-...     # 或把 key 放在项目根目录 open_router_api_key.txt
uvicorn api.main:app --reload --port 7860
```

打开 http://localhost:7860 。没有 key 也能跑到面板 ③（规则分类、指标、维度、候选），面板 ④ 需要 LLM。

## 部署（Hugging Face Spaces · Docker）

1. 新建 Space，SDK 选 Docker。
2. 把本仓库推上去（`.dockerignore` 已排除真实账单、key、缓存、评估结果）。
3. Settings → Variables and secrets 添加 `OPENROUTER_API_KEY`。
4. 可选：`MONEYBTI_MODEL_M3` / `_M6` / `_M7` / `_JUDGE` 按模块换模型（默认 M3/M6/M7 用 `deepseek/deepseek-v4-flash`，judge 用 `google/gemini-2.5-flash`）；`MONEYBTI_PROVIDER=bailian` 可切回阿里云百炼（key 用 `DASHSCOPE_API_KEY`）。

## 目录

```
core/   解析 · 规则分类 · 指标与维度 · 原型检索 · prompt · LLM 客户端 · 编排器
rag/    知识库：personas.json（23 卡 + 12 维 + 5 标签）、merchant_rules.json（20 商户家族）
api/    FastAPI：/api/upload /api/demo /api/confirm /api/generate /api/personas /api/samples
web/    前端（四个面板、对比视图、调试抽屉、档案票小票 + 21 张人格猫图、PNG 导出、中 / EN 双语）
tests/  20 个合成测试账单与真值；eval/ 评估脚本与结果
```
