<div align="center">

<img src="web/cats/app_icon2.webp" width="96" alt="MoneyBTI cat">

# 💰 MoneyBTI

**What did this month's money turn into?**

Turn a monthly bill into a spending persona you can actually read, and a persona ticket worth keeping.

🚀 [Live Demo](https://zhao1201-moneybti.hf.space) · 🤗 [Hugging Face Space](https://huggingface.co/spaces/Zhao1201/MoneyBTI) · ⚡ [Quick Start](#-quick-start)

**English** · [简体中文](README.zh-CN.md)

</div>

MoneyBTI is an AI spending-persona app. Import an Alipay or WeChat Pay bill, confirm the transaction categories, and discover your spending style: understand your habits, meet your own cat persona, and save the month as a retro ticket.

[![MoneyBTI home: bill import and analysis entry](assets/preview-upload.png)](assets/preview-upload.png)

## ✨ Features

| Feature | What you can do |
| --- | --- |
| 📥 Bill import | Upload or drag in CSV / XLSX bills exported from Alipay or WeChat Pay, follow the built-in export tutorial, or try the bundled demo bill. |
| ✅ Category review | Categories are assigned automatically; filter the transactions that need a look and fix them by hand before generating the result. |
| 📊 Spending profile | Category breakdown, a spending radar and candidate personas show your preferences and why each persona matches. |
| 🐱 Your persona | Get a cat persona card, a personal reading, spending traits and achievement badges that turn the bill into a fun monthly review. |
| 🎫 Ticket sharing | Switch between the Cream, Night Market and Mint themes, export a PNG, or copy the share text. |
| 📖 Persona gallery | Browse every persona's illustration, personality and traits, and explore spending styles beyond your own. |
| 🌐 Bilingual | Switch between Chinese and English, with persona readings and tickets in the matching language. |

### 🔍 Get to know your persona through your spending habits

Every persona card comes with its spending traits and a matching explanation. The result page places the persona reading next to the retro ticket so it is easy to review, keep and share.

[![Persona result with retro ticket: switch themes, copy text and export PNG](assets/preview-result.png)](assets/preview-result.png)

### 🎟️ Final output · the persona ticket

Once generation finishes, expand the ticket to see the full cat illustration, match score, achievement badges, spending traits and personal reading. Below is the complete ticket in the Cream theme; it can be exported straight to PNG.

<p align="center">
  <a href="assets/preview-ticket.png"><img src="assets/preview-ticket.png" width="480" alt="Full preview of a generated persona ticket: the Whale Warrior, with cat illustration, match score, badges and spending reading"></a>
</p>

<p align="center"><sub>Generated from a synthetic demo bill · click for the full-resolution ticket</sub></p>

### 📊 See your preferences and the reasoning behind the match

The category breakdown and spending radar help you read the bill at a glance; each candidate persona carries a matching explanation so the result is traceable. Before generating, you can go back to the category table and adjust transactions.

[![Spending profile: category breakdown, spending radar and candidate persona explanations](assets/preview-metrics.png)](assets/preview-metrics.png)

### 🐾 Explore the persona gallery

From everyday habits to strong lifestyle preferences, every persona has its own cat, description and style tags.

[![Persona gallery: cat illustrations, descriptions and style tags](assets/preview-gallery.png)](assets/preview-gallery.png)

<sub>Screenshots show the current UI with a synthetic demo bill, captured at 2x pixel density. Click any image for the full-resolution original.</sub>

## 📝 How to use

1. **📤 Import a bill**: open the app, upload an Alipay / WeChat Pay bill, or pick the bundled demo bill.
2. **✅ Confirm categories**: review the automatic categories and fix anything unclassified or ambiguous.
3. **📊 View the profile**: browse spending preferences, candidate personas and matching explanations.
4. **🎉 Generate and share**: generate your persona, pick a ticket theme, then save the image or copy the text.

Two analysis modes are available, and their results can be compared side by side:

| Mode | What it does |
| --- | --- |
| 🙂 Basic | Organises transactions with merchant rules, then generates the persona reading and share ticket. |
| 👑 VIP | Adds AI per-transaction semantic analysis on top of the rules, with a secondary persona and spending highlights. |

## 🚀 Quick start

### 🐍 Run locally

With Python 3.11, from the project root:

```bash
python -m venv .venv
```

Activate the virtual environment and set your OpenRouter API key.

**Windows PowerShell**

```powershell
.\.venv\Scripts\Activate.ps1
$env:OPENROUTER_API_KEY = "your API key"
```

**macOS / Linux**

```bash
source .venv/bin/activate
export OPENROUTER_API_KEY="your API key"
```

Install the dependencies and start the server:

```bash
python -m pip install -r requirements.txt
python -m uvicorn api.main:app --reload --port 7860
```

Open the [local app](http://localhost:7860) or the [API docs](http://localhost:7860/docs). Bill parsing, categorisation and the spending profile in Basic mode work without a key; AI persona copy and VIP per-transaction analysis need a configured model provider.

### 🐳 Docker

```bash
docker build -t moneybti .
docker run --rm -p 7860:7860 -e OPENROUTER_API_KEY moneybti
```

Set `OPENROUTER_API_KEY` in the current shell before running; the container reads it from the environment.

<details>
<summary>⚙️ Model provider configuration</summary>

OpenRouter is the default. Alibaba Cloud Bailian or any other OpenAI-compatible endpoint can be configured through environment variables.

| Variable | Purpose |
| --- | --- |
| `OPENROUTER_API_KEY` | OpenRouter API key. |
| `MONEYBTI_PROVIDER` | Provider: `openrouter` (default) or `bailian`. |
| `DASHSCOPE_API_KEY` | API key when using Bailian. |
| `MONEYBTI_BASE_URL` | Custom compatible endpoint; for Bailian, use the actual URL of your service. |
| `MONEYBTI_MODEL` | One model for every module. |
| `MONEYBTI_MODEL_M3` / `MONEYBTI_MODEL_M6` / `MONEYBTI_MODEL_M7` | Per-module models for transaction classification, persona copy and tone review; these override the shared setting. |

Defaults and the resolution logic live in [`core/llm.py`](core/llm.py).

</details>

## ⚙️ How it works

Bill parsing → automatic categorisation → user confirmation → spending profile and persona matching → AI reading → ticket rendering.

Bill cleaning, metric computation and candidate persona matching are done by code and rules; the AI writes the reading from those results. Generated copy is checked for numbers and wording, and falls back to preset copy when the review fails.

**🛠️ Stack**: FastAPI · Pandas / OpenPyXL · OpenAI SDK · vanilla JavaScript / CSS · Docker.

```text
api/       HTTP API and static page serving
core/      bill parsing, categorisation, profile metrics and the AI workflow
rag/       persona knowledge base and merchant classification rules
web/       UI, persona gallery and ticket rendering
assets/    project preview images
tests/     synthetic demo bills and test cases
eval/      evaluation scripts and development tooling
```

## 🔒 Data handling

- 🗑️ Uploaded bill files are deleted after parsing; analysis sessions are kept in server memory.
- 🙈 Names, account numbers and order IDs are never read as transaction fields. When AI features are used, the required transaction descriptions or aggregated features are sent to the configured model provider, and model calls are cached in the server-side `cache/` directory.
- 🎭 Personas are for observing spending habits and having fun. The match score reflects how well the rules fit; it is not a psychological assessment and not financial advice.

<sub>🎓 Built for the NTU PE6203 · Generative AI & Agentic AI course.</sub>
