# eval/ · Stage 6 评估流水线

```
python eval/build_personas_v4.py         # 从 docs_for_dev/人格设计 的 md 重建 rag/personas.json
python eval/gen_tests.py                 # 生成 tests/（22 个合成账单 + 真值）；--check 只复核
python eval/calibrate.py --real --tests  # 人格检索校准：v4 条件打分 vs v3 原型匹配，对照 expected.json
python eval/run_one.py tests/bills/T06.csv [basic|vip|A]   # 单账单全流程，看决策日志
python eval/run_variants.py --variants A,B,Bp,C --runs 2   # 跑变体，写 results/raw/*.json；--collect 只重建 runs.csv
python eval/judge.py --runs 2            # LLM judge 逐条打分（隐藏变体名），汇总 results.csv / results_summary.md
```

| 变体 | 定义 |
|---|---|
| A | 最小 LLM：脱敏原始行（不清洗）+ 一句话 prompt，无指标、无人格体系 |
| B | 普通版：规则分类 + 维度打分 + 原型匹配 + M6(basic) + 代码审查 + M7 |
| Bp | B'：B 的检索换成 v3 十二维原型匹配（其余相同；对照 v4 条件即维度） |
| C | VIP 版：规则预标注 + M3 逐笔 LLM + 原型匹配 + M6(vip) + 代码审查 + M7 |

| 指标 | 来源 |
|---|---|
| E1 人格正确性 | B / Bp / C：主人格代码 vs `expected.json`（自动）；A：judge 判 persona_match |
| E2 grounding | judge 0–2：文案数字与真值 ±3 pp，无编造类别 / 商户；VIP 字段与高光候选以系统自算结果为准 |
| E3 稳健安全 | min(自动规则检查, judge safety)：禁词、建议用语、禁止人格、data_level、清洗计数、confidence |
| E4 幽默清晰 | judge humor / clarity / share 各 1–5 |
| 辅助 | 分类准确率、未分类率（对照 `tests/labels`）、LLM 调用与 token、D5 兜底次数 |

所有 LLM 调用（含 judge）按内容哈希缓存在 `cache/`，同一轮的 salt 不同（run1 / run2、judge1 / judge2）保证是独立样本；重跑只会重放缓存。
`results/raw/` 每条运行一个 JSON（人格结果、审查、决策、每笔分类、指标摘要），`results/judge/` 每条 judge 输出，`results/logs/` 运行日志。

## UI 验收

```
uvicorn api.main:app --port 7860                 # 先起服务
python eval/ui_smoke.py T06 basic                # 走完四个面板，截图到 results/screens/，报告控制台错误
python eval/ui_smoke.py T06 vip --compare        # VIP + 对比模式
```
