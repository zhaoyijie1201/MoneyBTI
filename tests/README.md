# tests/ 合成测试集（Stage 6）

由 `python eval/gen_tests.py` 生成，全部合成数据，不含任何真实个人信息。

| 目录 / 文件 | 内容 |
|---|---|
| `bills/T01.csv … T22.csv`（T20 除外） | 支付宝格式 CSV（GBK 编码，23 行头部，与真实导出文件同结构）；T21 宠物、T22 月底渡劫人为 v4 新增 |
| `bills/T20.xlsx` | 微信格式 xlsx（含收入行、退款行、中性交易、转账） |
| `labels/Txx.json` | 每笔交易的真值类别，key = `time|merchant|amount`，值为 C1–C10；转账 / 收入 / 退款行为 null |
| `truth/Txx.json` | 按真值类别计算的 M5 指标、检索候选、预期行为（E2 grounding 的真值表） |
| `expected.json` | 22 个用例的预期主人格 / 禁止人格 / 清洗计数 / 数据等级（E1、E3 自动比对；v4 人格代码） |

`python eval/gen_tests.py --check` 只做一致性检查，不重新生成。
