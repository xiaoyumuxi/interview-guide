# Hard Dev 最终定点独立复审报告

## 复审声明

- 复审对象：`hard-dev-draft.jsonl` 中修订后的 `hard_dev_025` 与 `hard_dev_046`。
- 复审性质：`AGENT_REVIEWED_NOT_HUMAN`，不是人工审核。
- 复审方式：独立核对当前样本，不修改数据，不沿用此前的通过/拒绝结论。
- 执行边界：Test 仅用于只读泄漏检查；未执行 Test、embedding 或 retrieval。

## 结论

| Sample | 当前 QueryType | Gold 数量 | Decision | 关键结论 |
|---|---:|---:|---|---|
| `hard_dev_025` | `PARAPHRASE` | 1 | APPROVE | 类型已与单个真实 Section 一致；Gold 完整支撑版本差异、单线程范围及原因。 |
| `hard_dev_046` | `MULTI_SECTION` | 3 | APPROVE | 三个真实 Section 分别支撑雪崩、穿透、击穿的场景化措施，关系明确且均不可替代。 |

最终结果：2/2 APPROVE，无待修复项。

## 九项质量检查

两条样本均通过：

1. `question_naturalness`
2. `evidence_grounding`
3. `answer_grounding`
4. `difficulty`
5. `gold_uniqueness`
6. `negative_quality`
7. `multi_section_relation`
8. `offset_replay`
9. `test_leakage`

其中 `hard_dev_025` 不是 Multi-Section 或 Hard Negative，`hard_dev_046` 不是 Hard Negative；对应不适用项按“类型与结构一致、无不合格负证据”通过，不代表存在负证据或多段关系。

## Offset 与 Test 泄漏

- Offset replay：4/4 Gold Evidence 均满足 `normalized.md[start_offset:end_offset] == evidence.text`。
- Evidence hash：未与只读 Test 重复。
- Section：未与只读 Test 重复。
- Offset span：未与只读 Test 重叠。
- Reference Answer：未直接复用只读 Test。
- Question：最高归一化相似度分别为 0.1967 与 0.1481，均未达到近似改写阈值 0.90。

## 执行状态

```text
Test execution: NOT EXECUTED
Embedding: NOT EXECUTED
Retrieval: NOT EXECUTED
Test used for: READ_ONLY_LEAKAGE_AUDIT
Review kind: AGENT_REVIEWED_NOT_HUMAN
```
