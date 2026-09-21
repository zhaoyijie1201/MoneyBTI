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

上传支付宝 / 微信月账单，代码算指标与消费维度，规则从 21 张人格原型 + 3 枚成就徽章中筛出候选，AI 只在候选内挑选并写文案 —— 输出带匹配度与雷达图的「花钱人格」，以及一张可导出分享的复古小票。NTU PE6203 *Generative AI & Agentic AI* 小组作业项目。

## 🔗 Project

🌐 在线体验（Hugging Face Space）：https://zhao1201-moneybti.hf.space

🐙 GitHub：https://github.com/zhaoyijie1201/MoneyBTI

🤗 Hugging Face Space：https://huggingface.co/spaces/Zhao1201/MoneyBTI

## 功能特色

- **两种档位**：普通版（规则分类 + 商户映射）、VIP 版（逐笔 LLM 语义分析 + 时间维度）
- **人格判定**：12 维消费指标 → 21 张常规人格 + 3 枚特殊徽章（全勤打工人 / 一日暴走 / 薅羊毛大师），条件打分而非单一阈值，规则先圈定候选，AI 只在候选内二选一并写文案（"代码判分、AI 写作"，避免幻觉）
- **可解释输出**：匹配度百分比、12 维雷达图、命中条件排行、規則 + LLM 双重安全审查
- **复古小票**：姓名 / 匹配度 / 人格解读 / 特质 / 徽章 / 消费指数，一键导出 PNG、可分享
- **中 / 英双语**：界面、知识库（人格卡 + 商户规则）、生成文案均支持语言切换
- **可复现评估**：A（无结构基线）/ B（普通版）/ B'（原型匹配对照）/ C（VIP 版）四变体，LLM judge 打分 + 规则自动核验

## 处理流程

```
上传账单 → 解析清洗 → 规则/LLM 分类商户与类别 → 计算 12 维消费指标
        → 规则圈定候选人格（条件打分） → AI 在候选内选择并生成文案
        → 代码规则审查 + LLM 复核（M7） → 雷达图 + 小票渲染
```

## 本地运行

```bash
pip install -r requirements.txt
set OPENROUTER_API_KEY=sk-or-...     # 或把 key 放在项目根目录 open_router_api_key.txt
uvicorn api.main:app --reload --port 7860
```

打开 http://localhost:7860 。没有 key 也能跑到面板 ③（规则分类、指标、维度、候选），面板 ④ 生成人格文案需要 LLM。

## 部署（Hugging Face Spaces · Docker）

1. 新建 Space，SDK 选 Docker。
2. 把本仓库推上去（`.dockerignore` 已排除真实账单、key、缓存、评估结果）。
3. Settings → Variables and secrets 添加 `OPENROUTER_API_KEY`。
4. 可选：`MONEYBTI_MODEL_M3` / `_M6` / `_M7` / `_JUDGE` 按模块换模型（默认 M3/M6/M7 用 `deepseek/deepseek-v4-flash`，judge 用 `google/gemini-2.5-flash`）；`MONEYBTI_PROVIDER=bailian` 可切回阿里云百炼（key 用 `DASHSCOPE_API_KEY`）。

## 目录结构

```
core/   解析 · 规则分类 · 12 维指标 · 人格候选检索 · prompt · LLM 客户端 · 编排器
rag/    知识库：personas.json（21 人格卡 + 3 徽章 + 12 维度）、merchant_rules.json（21 商户家族）
api/    FastAPI：/api/upload /api/demo /api/confirm /api/generate /api/personas /api/samples
web/    前端：四面板 UI、对比视图、调试抽屉、复古小票（PNG 导出）、中 / EN 双语
tests/  22 个合成测试账单与人工真值
eval/   A/B/B'/C 变体评估脚本、LLM judge、UI 冒烟测试
```

## 评估结果（44 组，LLM judge 隐藏变体打分）

| 变体 | 人格正确率 | grounding (0–2) | 安全 (0–2) | 分类准确率 | LLM 调用/账单 | token/账单 |
|---|---|---|---|---|---|---|
| A 最小 LLM 基线 | 4% | 0.42 | 1.75 | — | 0.95 | 3,136 |
| B 普通版 | 100% | 1.92 | 1.95 | 91% | 1.91 | 5,008 |
| B' 原型匹配对照 | 91% | 1.85 | 2.00 | 91% | 1.77 | 4,002 |
| C VIP 版 | 100% | 1.69 | 1.95 | 94% | 4.5 | 24,058 |

规则驱动候选（B/C）相比纯 LLM 基线（A）大幅提升人格判定准确率与安全性；详见 `eval/README.md`。

## 技术栈

FastAPI · Uvicorn · Pandas/OpenPyXL（账单解析）· OpenAI SDK（OpenRouter / 阿里云百炼兼容接口）· 原生 JS/CSS 前端 · Docker（Hugging Face Spaces）
