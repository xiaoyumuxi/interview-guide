# Phase 1.5 Audit Fix Report

## 1. 修复内容

### CSV 身份字段覆盖

`hard-negative-analysis.csv` 原导出器先写入 `experiment_id/dataset/strategy`，
随后又按完整 fields 展开空 Metric 值，导致身份字段被覆盖。身份字段现与 Metric
字段分离构造，并在导出后强制检查非空。新 CSV 为 12 行，每行四个身份字段
（含 `group`）均非空。

### Hard Negative 有效分母

Metric V2 新增：

```text
HardNegativeQueryCount
NegativeBearingQueryCount
GoldMappedQueryCount
NegativeMappedQueryCount
MarginEligibleQueryCount
PairwiseComparisonCount
```

并同时输出 `PairwiseGoldWinCount`、`GoldBeforeNegativeSuccessCount@K` 与
`GoldBeforeNegativeQueryCount@K`。Margin、Pairwise 和 Gold-before-negative
不再只展示比率，而是能回放其真实有效分母。

### NEGATIVE_BEARING 派生分组

`NEGATIVE_BEARING` 由 `bool(sample.negative_evidences)` 动态生成，不修改原始
Query Type。Current Dev 的 9 条带负证据样本恰好都属于 HARD_NEGATIVE；Hard
Query Dev 中 HARD_NEGATIVE 为 15 条，但 NEGATIVE_BEARING 实际有 26 条。

### Token 口径

Phase 1 正则分词被明确封装为 `LexicalApproxTokenizer` /
`LexicalApproxTokenCounter`。它继续决定既有 Chunk 和 Context budget，从而保证
Chunk boundary 与质量实验不变。新增 `HuggingFaceTokenCounter`，只用本地
`Qwen/Qwen3-Embedding-0.6B` Tokenizer 对已有文本重计数。

本次本地 Qwen Tokenizer 加载成功，`token_count_mode=huggingface`。若本地
Tokenizer 不存在，只允许离线 fallback，并输出
`TOKENIZER_FALLBACK_TO_APPROXIMATE` 与 `token_count_mode=approximate`。

### Cold / Warm 性能

原结果把 S1 cold subquery cache 与 S2 warm cache 放在同一横向表中。审计修复后：

- Cold：每个 dataset/scheme 使用独立空 Query cache；
- Warm：计时前为每个 scheme 预载完全相同的 Original + Subquery 集合；
- 文档 embedding 复用原 cache，不计入 Query latency；
- 正式横向比较只使用 Warm；
- S3 latency 包含 ContextAssembler，S0–S2 只包含 retrieval。

当前工具环境的 MPS 后端在审计执行时不可用，因此 Cold/Warm **统一在 CPU**
重测；原质量指标仍是既有 MPS 结果。两个设备在 raw metadata 中分别记录，未混为
一次运行。

### 实验元数据

新增 `build_experiment_metadata()`，统一记录 21 个必需字段。更新后的 ablation
raw 顶层包含 `test_executed=false`、Git commit、两个 dataset 的组合 SHA、
corpus manifest SHA、模型/Tokenizer/设备/平台/seed 等。

更新 raw 保存原质量指标 SHA，标记：

```text
quality_metrics_reexecuted = false
quality_metrics_source_experiment_id = 20260728T100028Z-multisection-ablation
```

### Hard Query Dev 定位

所有面向用户的材料现明确：Hard Query Dev Set / Query Stress Set 复用 Dev
Evidence Pool，用更隐式复杂的表达测量 Query Difficulty 与 Retrieval
Robustness；它不衡量新文档或新主题泛化，也不具备独立留出评估含义。

## 2. 测试结果

```text
pytest: 37 passed
python -m compileall src scripts: PASS
```

新增测试覆盖 CSV identity、NEGATIVE_BEARING、有效映射计数、Pairwise/GBN
分母、Qwen Tokenizer、离线 fallback、Chunk boundary 不变、Warm cache preload、
元数据完整性以及 `test_executed=false`。

## 3. Hard Negative 新结果

### Current Dev

Current Dev 的 HARD_NEGATIVE 与 NEGATIVE_BEARING 均为同一组 9 条：

| Strategy | Group | Q | Gold mapped | Neg mapped | Margin eligible | Pairwise win | Gold before neg@5 | Exposure@5 | Avg margin |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Fixed | HARD_NEGATIVE | 9 | 9 | 9 | 9 | 18/20 = 0.9000 | 7/9 = 0.7778 | 0.4444 | 0.0990 |
| Fixed | NEGATIVE_BEARING | 9 | 9 | 9 | 9 | 18/20 = 0.9000 | 7/9 = 0.7778 | 0.4444 | 0.0990 |
| Structure | HARD_NEGATIVE | 9 | 9 | 9 | 9 | 20/20 = 1.0000 | 9/9 = 1.0000 | 0.2222 | 0.1504 |
| Structure | NEGATIVE_BEARING | 9 | 9 | 9 | 9 | 20/20 = 1.0000 | 9/9 = 1.0000 | 0.2222 | 0.1504 |
| Parent-Child | HARD_NEGATIVE | 9 | 4 | 4 | 2 | 2/2 = 1.0000 | 4/9 = 0.4444 | 0.0000 | 0.1741 |
| Parent-Child | NEGATIVE_BEARING | 9 | 4 | 4 | 2 | 2/2 = 1.0000 | 4/9 = 0.4444 | 0.0000 | 0.1741 |

Parent-Child 的 1.0 Pairwise 只来自 2 次有效比较，不能与 Structure 的 20/20
等量解释。

### Hard Query Dev Set

| Strategy | Group | Q | Gold mapped | Neg mapped | Margin eligible | Pairwise win | Gold before neg@5 | Exposure@5 | Avg margin |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Fixed | HARD_NEGATIVE | 15 | 15 | 15 | 15 | 18/20 = 0.9000 | 11/15 = 0.7333 | 0.3333 | 0.1130 |
| Fixed | NEGATIVE_BEARING | 26 | 26 | 26 | 26 | 33/39 = 0.8462 | 17/26 = 0.6538 | 0.3462 | 0.0868 |
| Structure | HARD_NEGATIVE | 15 | 15 | 15 | 15 | 19/20 = 0.9500 | 11/15 = 0.7333 | 0.1333 | 0.1553 |
| Structure | NEGATIVE_BEARING | 26 | 26 | 26 | 26 | 34/39 = 0.8718 | 20/26 = 0.7692 | 0.1538 | 0.1298 |
| Parent-Child | HARD_NEGATIVE | 15 | 9 | 7 | 4 | 4/4 = 1.0000 | 4/15 = 0.2667 | 0.0000 | 0.2093 |
| Parent-Child | NEGATIVE_BEARING | 26 | 14 | 10 | 5 | 5/5 = 1.0000 | 7/26 = 0.2692 | 0.0000 | 0.1874 |

## 4. Token 对照

仅重计数已有 indexable chunks，`chunk_boundaries_changed=false`：

| Strategy | Chunks | Approx avg | Qwen avg | Approx P95 | Qwen P95 |
|---|---:|---:|---:|---:|---:|
| Fixed | 889 | 499.1 | 439.5 | 512 | 571 |
| Structure | 1,328 | 286.6 | 251.8 | 504 | 494 |
| Parent-Child | 5,475 | 69.5 | 60.9 | 226 | 189 |

“512”只代表旧 lexical approximate boundary，不等于 Qwen 的 512 tokens；Fixed
的 Qwen P95 反而达到 571。

## 5. 性能对照

### Current Dev（CPU）

| Scheme | Cold hit/miss | Cold P50/P95 ms | Warm hit/miss | Warm P50/P95 ms |
|---|---:|---:|---:|---:|
| S0 | 0/73 | 267.6 / 376.5 | 73/0 | 0.115 / 0.122 |
| S1 | 0/117 | 311.8 / 1020.9 | 117/0 | 0.132 / 0.663 |
| S2 | 0/117 | 318.2 / 1054.4 | 117/0 | 0.127 / 0.679 |
| S3 | 0/117 | 326.9 / 1117.3 | 117/0 | 1.227 / 1.627 |

### Hard Query Dev（CPU）

| Scheme | Cold hit/miss | Cold P50/P95 ms | Warm hit/miss | Warm P50/P95 ms |
|---|---:|---:|---:|---:|
| S0 | 0/48 | 448.1 / 532.5 | 48/0 | 0.132 / 0.142 |
| S1 | 0/77 | 506.5 / 1380.2 | 77/0 | 0.137 / 0.612 |
| S2 | 0/77 | 531.5 / 1327.4 | 77/0 | 0.138 / 0.609 |
| S3 | 0/77 | 524.4 / 1301.0 | 77/0 | 1.576 / 2.361 |

S1/S2 的 Warm retrieval latency 接近，证明原先的巨大差异主要来自 cache 状态不等。
但 Multi-Query 仍需要 117 vs 73（Current Dev）和 77 vs 48（Hard Query Dev）
query embeddings/retrieval calls，成本结论不变。

## 6. 核心结论是否改变

不改变：

1. Structure 在 Agent-reviewed Current Dev 上优于 Fixed。
2. Fixed 在复用 Dev Evidence 的 Hard Query Dev / Query Stress Set 上严格 Recall
   更稳，但这不是独立泛化结论。
3. Parent-Child 的严格 Coverage 较差；其漂亮的负样本比率受极小有效分母影响。
4. 当前这版规则 Query Decomposition + RRF 没有通过上线门槛；这不表示所有
   Multi-Query 方法普遍无效。

质量实验没有重新执行，Test 没有运行。
