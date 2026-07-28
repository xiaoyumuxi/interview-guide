# Hard Dev 修订样本独立复审报告

## 复审声明

- 复审对象：`hard-dev-draft.jsonl` 中 12 条指定修订样本。
- 复审性质：`AGENT_REVIEWED_NOT_HUMAN`，不是人工审核。
- 复审方式：从当前样本与真实 Markdown 上下文重新判断，不沿用首轮结论。
- 边界：只读检查 Test；未修改数据，未运行 Test、embedding 或 retrieval。

## 结果

- APPROVE：10 条
- REJECT：2 条
- Offset replay：12/12 样本全部通过，所有 Gold 与 Negative span 均与对应 `normalized.md[start_offset:end_offset]` 精确一致。
- Test 泄漏：12/12 通过；未发现与只读 Test 的问题完全重复或 Evidence ID 重叠。

| Sample | Decision | 关键结论 |
|---|---|---|
| `hard_dev_007` | APPROVE | 新增并发约束后能区分 ConcurrentHashMap；负证据会漏掉线程安全要求。 |
| `hard_dev_009` | APPROVE | CLH 负证据与 AQS 同簇，但不能解释通用模板骨架。 |
| `hard_dev_025` | REJECT | 单个 Gold Section 仍标为 `MULTI_SECTION`。 |
| `hard_dev_026` | APPROVE | 两条 Gold 完整解释定期删除与访问时删除。 |
| `hard_dev_027` | APPROVE | 过期判定数据结构与清理策略职责区分清楚。 |
| `hard_dev_029` | APPROVE | ACK/SACK 数值推理唯一且完整。 |
| `hard_dev_030` | APPROVE | 累计 ACK 与 SACK block 术语辨析有直接依据。 |
| `hard_dev_031` | APPROVE | 三段关闭报文的合并条件完整。 |
| `hard_dev_032` | APPROVE | 应用关闭时机与延迟 ACK 条件均不可省略。 |
| `hard_dev_033` | APPROVE | select 线性扫描有唯一 Gold；poll 是有效近邻负证据。 |
| `hard_dev_037` | APPROVE | XA、TCC、Saga 三个 Section 构成真实机制对照。 |
| `hard_dev_046` | REJECT | 标为 `HARD_NEGATIVE`，但没有任何 Negative Evidence。 |

## 九项检查口径

每条样本均重新检查：

1. `question_naturalness`
2. `evidence_grounding`
3. `answer_grounding`
4. `difficulty`
5. `gold_uniqueness`
6. `negative_quality`
7. `multi_section_relation`
8. `offset_replay`
9. `test_leakage`

逐条布尔结果、说明与必要修复项见 `rereview-decisions.jsonl`。

## 待修订项

### `hard_dev_025`

当前只有一个真实 Markdown Section，却保留 `MULTI_SECTION` 类型。应改为合适的非 Multi-Section 类型，或新增对答案不可替代、具有真实逻辑关系的第二个 Dev Gold Section。

### `hard_dev_046`

当前三个 Gold 适合作为 Multi-Section 对照，但样本仍标为 `HARD_NEGATIVE` 且负证据为空。应改为 `MULTI_SECTION`，或补充有效的同概念簇 Hard Negative。
