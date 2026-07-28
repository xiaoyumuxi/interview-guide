# Phase 1 Chunking Benchmark Report

## 结论状态

真实语料 Dev 实验已跑完，Structure-Aware 当前综合最好。按用户要求，两个审核子智能体
逐条审核了 Dev 80 与 Test 40；首次拒绝 7 条，修复并定向复审后达到 Dev 80/80、
Test 40/40 `AGENT_APPROVED`。这不是人工审核，Test 从未运行，也未冻结。因此下列指标
仍是 **agent-reviewed Dev 结果**，不能包装成最终 Test 结论。

本阶段没有修改 Fixed、Structure-Aware、Parent-Child 或 Metric 实现。

## 两套结果必须分开

### Synthetic Smoke Test

实验 `20260728T065728Z-37412` 只验证数据流正确性，不用于选型或简历。

| Strategy | Chunks | Recall@5 | MRR |
|---|---:|---:|---:|
| Fixed | 25 | 0.9603 | 0.8767 |
| Structure-Aware | 50 | 0.9841 | 0.9762 |
| Parent-Child | 100 | 0.9444 | 0.9269 |

### java-interview-real-v1 Provisional Dev

实验 `20260728T083734Z-47450` 使用本地
`Qwen/Qwen3-Embedding-0.6B`，不是 hashing/mock。

| Strategy | Chunks | Recall@1 | Recall@3 | Recall@5 | Recall@10 | MRR |
|---|---:|---:|---:|---:|---:|---:|
| Fixed 512/64 | 889 | 0.7237 | **0.9635** | 0.9635 | **0.9909** | 0.8832 |
| Structure-Aware | 1,328 | **0.7922** | 0.9018 | **0.9749** | 0.9840 | **0.9030** |
| Parent-Child | 5,475 | 0.7283 | 0.8767 | 0.8881 | 0.9658 | 0.8732 |

Structure 相对 Fixed：

- Recall@1：+6.85 个百分点；
- Recall@5：+1.14 个百分点；
- MRR：+1.97 个百分点；
- Chunk / index 规模：约 +49.4%。

Structure 并非所有 K 都占优：Fixed 的 Recall@3 和 Recall@10 更高。当前目标侧重
Top-5 和首个相关结果排名，因此 Structure 是当前推荐，而不是全指标碾压。

Parent-Child 的 5,475 个子 Chunk 约为 Fixed 的 6.16 倍，但 Recall@5 与 MRR 都更低，
当前配置没有展示出足以覆盖其成本的收益。

## 实验身份

- Experiment ID：`20260728T083734Z-47450`
- Dataset：`java-interview-real-v1-dev-agent-reviewed`
- Dev SHA-256：`2a45aa75709ee11bb27552d0cfb3f27939e95f01de551913cc9823649410cc37`
- Documents：48
- Dev：80（73 answerable，7 unanswerable）
- Test：40，`AGENT_APPROVED`、非人工、未冻结，**NOT EXECUTED**
- Embedding：`Qwen/Qwen3-Embedding-0.6B`
- Dimensions：1024
- Device：Apple MPS
- Retriever：NumPy exact cosine
- Top-K：1、3、5、10
- Cloud API：关闭

原始结果：

- `results/raw/20260728T083734Z-47450.json`
- `results/reports/java-interview-real-v1-agent-reviewed.csv`

## 正式语料与数据集

48 篇原始 Markdown 固定于：

- JavaGuide commit `8fb36af2bcd92d87c5223214980a9a97ef946f10`
- advanced-java commit `1659850d7de4739ac9394dddd6c68466a8c38761`

审计剔除了 3 篇推广/导航页。每份保留文档都记录 URL、commit、license、relative path
和 file SHA-256；上游全文不提交到本仓库。

```text
48 real Markdown files
  -> 180 agent-authored candidates
  -> strict offset / grounding / provenance gates
  -> Qwen question embedding deduplication (threshold 0.90)
  -> 120 subagent release-reviewed samples
  -> leakage-grouped Dev 80 / Test 40
```

最终 120 条类型分布：

| Type | Total | Dev | Test |
|---|---:|---:|---:|
| Direct Fact | 32 | 21 | 11 |
| Paraphrase | 28 | 19 | 9 |
| Terminology | 18 | 12 | 6 |
| Multi-Section | 18 | 12 | 6 |
| Hard Negative | 14 | 9 | 5 |
| Unanswerable | 10 | 7 | 3 |

Dev 和 Test 均覆盖 12 类且均包含 advanced-java Evidence。gold Evidence、Hard Negative
完整负 Evidence、Section、文本哈希和实际 offset 区间跨 split 都无交叉。

所有问题和答案均未通过项目内 LLM 生成；`generator_model` 全为空。子智能体依据固定
Evidence 编写，Qwen 只承担语义去重与检索向量化。

## 分类型结果

下表为 Recall@5 / MRR：

| Query Type | Fixed | Structure | Parent-Child |
|---|---:|---:|---:|
| Direct Fact | 0.9524 / 0.8639 | **1.0000 / 0.9206** | 1.0000 / 0.8968 |
| Paraphrase | 1.0000 / 0.8509 | **1.0000 / 0.8991** | 0.8947 / 0.8825 |
| Terminology | 1.0000 / 0.9028 | **1.0000 / 1.0000** | 1.0000 / 0.9583 |
| Multi-Section | **0.8611 / 0.9583** | 0.8472 / 0.7083 | 0.4861 / 0.7897 |
| Hard Negative | 1.0000 / 0.8704 | **1.0000 / 1.0000** | 1.0000 / 0.7963 |

Structure 的总体收益主要来自 Direct、Paraphrase、Terminology 和 Hard Negative；
Multi-Section 明显退化，是冻结 Test 前必须继续检查的风险点。

当前 Metric 只衡量 gold Evidence retrieval。Hard Negative 的两个同概念簇负 Evidence
已经内嵌并可回放，但现有 Metric 按用户约束未修改，因此本报告不声称已经测量
“负 Evidence 排除率”。Unanswerable 同样不计入普通 dense retrieval 的 Recall/MRR。

## 成本

下表的首次向量化成本取自同一问题/Gold Evidence 的冷缓存运行
`20260728T075511Z-44545`；代审版运行复用了这些向量，因此不以其暖缓存毫秒数代表
首次成本。7 条审核修复只涉及 Reference Answer 或负 Evidence，不改变下表检索输入。

| Strategy | Avg tokens | P50 | P95 | Index estimate | New document embeddings | Embedding time |
|---|---:|---:|---:|---:|---:|---:|
| Fixed | 499.07 | 512 | 512 | 3,641,344 B | 889 | 269.77 s |
| Structure | 286.59 | 285 | 504 | 5,439,488 B | 1,328 | 355.86 s |
| Parent-Child | 69.51 | 51 | 226 | 22,425,600 B | 5,212 | 482.69 s |

三组共享 73 个 answerable query embedding。耗时是本机首次/部分冷缓存记录，不能当作
跨机器吞吐基准；Chunk 数和索引估算更适合比较长期成本。

## 当前建议

1. 保留 Fixed 作为生产 A/B baseline。
2. 将 Structure-Aware 作为 Java / Spring AI 原型候选。
3. 暂不迁移当前 Parent-Child 配置。
4. 当前只使用 Agent-reviewed Dev 调参；Test 保持未运行、未冻结。
5. 若要求严格人工金标，再由真实审核者复核后冻结 Test。
6. 最终配置只在冻结 Test 上执行一次。
7. 在进入 Hybrid、Reranker 或 HNSW 前，先解释并改善 Multi-Section 退化。
