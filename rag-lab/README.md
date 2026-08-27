# rag-lab

`rag-lab` 是 InterviewGuide RAG 模块的独立离线实验环境。它只做文档转换、Evidence
数据集、Chunk 对照、Embedding、精确检索和离线评测，不提供面向业务用户的 Web 服务、
用户系统、对话系统或知识库管理。Phase 2 额外提供仅用于本地实验分析的 Evaluation
Workbench。

Phase 1 固定比较三种策略：

- Fixed 512/64
- Markdown Structure-Aware
- Parent-Child

Ground Truth 绑定 normalized Markdown 的 `document_id + [start_offset, end_offset)`，
不绑定任何 Chunk ID，因此同一数据集可以公平评测不同切块边界。

## 数据流

```text
PDF / DOCX / Markdown / HTML / TXT
  -> MarkItDown adapter
  -> normalized Markdown
  -> markdown-it AST + source offsets
  -> evidence-first JSONL
  -> Fixed / Structure-Aware / Parent-Child
  -> local Qwen embedding + SQLite cache
  -> NumPy exact cosine search
  -> AnyOverlap / Evidence Coverage & Recall / Context Precision / Hard Negative metrics
```

除向量化外，Phase 1/1.5 正式数据构建不调用本地或远程生成模型。题目与简洁 Reference
Answer 已由子智能体基于固定真实 Evidence 编写并保存为草稿；Qwen 只用于问题语义去重和检索。
Phase 2 的生成评测是独立可选层，不改变现有 Retrieval Ground Truth 与指标定义。

## 安装

需要 Python 3.11+ 和 [uv](https://docs.astral.sh/uv/)。

```bash
cd rag-lab
UV_CACHE_DIR=.uv-cache uv sync --extra dev --extra qwen
```

正式实验使用本地 `Qwen/Qwen3-Embedding-0.6B`、1024 维向量和 Apple MPS。
配置保持 `local_files_only: true`；缺少模型会明确失败，不会回退到 mock 或云 API。

## 两套数据

### synthetic-smoke-v1

模板化合成笔记只用于验证 Chunker、Evidence offset、Metric、cache 和 Runner 是否正常。
其结果不得写入简历或作为方案选型证据。

```bash
UV_CACHE_DIR=.uv-cache uv run python scripts/seed_demo_corpus.py
UV_CACHE_DIR=.uv-cache uv run python scripts/benchmark_chunking.py \
  --config configs/baseline.yaml
```

### java-interview-real-v1

正式语料是两个固定 commit 下的 48 篇原始 Markdown，覆盖 Java 基础、集合、JUC、JVM、
Spring、MySQL、Redis、网络、操作系统、分布式、消息队列和系统设计：

- `Snailclimb/JavaGuide`：Apache-2.0
- `doocs/advanced-java`：CC-BY-SA-4.0

仓库 URL、commit、license、相对路径和文件 SHA-256 记录在
[`NOTICE-SOURCES.md`](NOTICE-SOURCES.md)。下载仓库和物化后的完整原文被 `.gitignore`
排除，不提交到 `rag-lab`。

准备固定语料：

```bash
git clone https://github.com/Snailclimb/JavaGuide.git data/sources/JavaGuide
git -C data/sources/JavaGuide checkout 8fb36af2bcd92d87c5223214980a9a97ef946f10
git clone https://github.com/doocs/advanced-java.git data/sources/advanced-java
git -C data/sources/advanced-java checkout 1659850d7de4739ac9394dddd6c68466a8c38761
UV_CACHE_DIR=.uv-cache uv run python scripts/prepare_java_interview_corpus.py
```

候选草稿在 `data/datasets/java-interview-real-v1/agent-drafts/`。构建正式待审数据时，
Qwen embedding 只用于 0.90 阈值的语义去重：

```bash
UV_CACHE_DIR=.uv-cache uv run python scripts/merge_agent_dataset_drafts.py --device mps
UV_CACHE_DIR=.uv-cache uv run python scripts/validate_java_real_dataset.py
```

机器门禁要求：

- 180 条候选，保留 120 条；
- Dev 80 / Test 40，类型配额固定；
- gold 与 hard-negative Evidence 严格等于 normalized Markdown offset 切片；
- Dev/Test 均覆盖 12 类并包含两个来源；
- Evidence ID、Section、文本和实际 offset 区间跨 split 零泄漏；
- `generator_model` 全为空；
- 初始 Test 保持 `PENDING_HUMAN`，不得自动伪装成人工冻结。

## 审核与冻结

项目提供子智能体代审版：Dev 80/80、Test Candidate 40/40 均通过逐条 release
review。最终 Test 又由独立审核智能体完成 40/40 复核和 53/53 Evidence 回放，
随后按 `AGENT_REVIEWED_NOT_HUMAN` 冻结。它不是人工金标。

按用户授权，冻结 Test 已于 2026-07-28 只执行一次，实验 ID 为
`20260728T115625Z-57404`；执行账本会拒绝再次运行，防止用 Test 继续调参。

如仍需满足严格的“真人审核”要求，可运行：

```bash
UV_CACHE_DIR=.uv-cache uv run python scripts/review_and_freeze_test.py \
  --split dev --reviewer YOUR_NAME
UV_CACHE_DIR=.uv-cache uv run python scripts/review_and_freeze_test.py \
  --split test --reviewer YOUR_NAME
```

若仍需满足严格的真人审核要求，应另行复核，不能把当前智能体冻结改称人工冻结。
正式调参仍只能使用 Dev；已执行的 Test 不得用于反复调参。

## Phase 1.5：严格评测

Metric V2 使用按文档合并的 source span，默认 50% coverage 才算 Evidence 命中，
并将 embedding text 与 evaluation source text 分离：

```bash
UV_CACHE_DIR=.uv-cache uv run python scripts/benchmark_chunking.py \
  --config configs/experiments/qwen-java-interview-real-v1-metrics-v2.yaml
```

Hard Query Dev Set 有 48 条，12 个类别各 4 条，最终状态为
`AGENT_REVIEWED_NOT_HUMAN`。审核历史保留首轮 12 个 REJECT 和两轮独立复审：

它复用 Current Dev Evidence Pool，仅使用更隐式、场景化和多段的问题表达来测量
Query Difficulty 与 Retrieval Robustness；它不是独立留出集，也不衡量新文档或
新主题泛化。

```bash
UV_CACHE_DIR=.uv-cache uv run python scripts/validate_hard_dev.py
UV_CACHE_DIR=.uv-cache uv run python scripts/benchmark_chunking.py \
  --config configs/experiments/qwen-java-interview-hard-dev.yaml
```

Multi-Section S0/S1/S2/S3：

```bash
UV_CACHE_DIR=.uv-cache uv run python scripts/run_multisection_ablation.py \
  --config configs/experiments/qwen-java-interview-multisection-ablation.yaml
```

Current Dev Metric V2 中，Structure-Aware 的 EvidenceRecall@5/50 为 `0.9658`，
高于 Fixed 的 `0.9361`；Hard Query Dev 中 Fixed 为 `0.7812`，反而高于 Structure 的
`0.7118`。当前规则 Multi-Query 在 Current Dev Multi-Section 将 AllEvidenceHit@5
从 `0.5833` 降到 `0.3333`，因此不建议上线。

一次性冻结 Test 上，Fixed / Structure 的 EvidenceRecall@5/50 均为 `0.9459`；
Structure 的 Coverage@5、ContextPrecision@5、MRR 分别为 `0.9457`、`0.1882`、
`0.9052`，均高于 Fixed 的 `0.9220`、`0.1200`、`0.7601`。Parent-Child 的
EvidenceRecall@5/50 仅为 `0.6892`。完整边界与结果见
[`docs/FINAL-TEST-REPORT.md`](docs/FINAL-TEST-REPORT.md)。

输出：

- `results/raw/<experiment-id>.json`：配置、环境、数据 SHA、分类型指标和成本；
- `results/reports/metrics-v2-comparison.csv`：Current Dev 三种 Chunker 严格指标；
- `results/reports/hard-dev-comparison.csv`：Hard Query Dev 三种 Chunker；
- `results/reports/multisection-ablation.csv`：S0/S1/S2/S3；
- `results/reports/hard-negative-analysis.csv` 与
  `context-quality-comparison.csv`：负样本和 Context 分析；
- `results/reports/token-count-comparison.csv`：旧 lexical approximate 与
  Qwen Tokenizer 的只读重计数，不改变 Chunk boundary；
- `results/reports/ablation-performance-{cold,warm}.csv`：隔离 Cold cache
  与统一预热 Warm cache 的性能结果，横向比较只使用 Warm；
- `data/datasets/java-interview-real-v1/*-agent-reviewed.jsonl`：代审 Dev/Test；
- `data/datasets/java-interview-real-v1/test-agent-frozen.jsonl`：智能体复核冻结 Test；
- `results/test/AGENT-FROZEN-TEST-EXECUTION.json`：一次性 Test 执行账本；
- `results/reports/agent-frozen-test-final.csv`：冻结 Test 三策略结果；
- `results/reports/synthetic-smoke-v1.csv`：仅 Smoke Test；
- `data/cache/*.sqlite3`：以模型、维度、文本类型和 SHA-256 为键的向量缓存。

完整结论与限制见
[`docs/PHASE1.5-REPORT.md`](docs/PHASE1.5-REPORT.md) 和
[`docs/SPLIT-AUDIT.md`](docs/SPLIT-AUDIT.md)。

## Phase 2：生成评测与 Workbench

Phase 2 在现有 Retrieval Runner 后增加可选 Generation Evaluation，不改变 Phase 1.5
检索指标。`generation.enabled: false` 时旧实验行为保持不变；开启后会将 Top-K Context
送入 OpenAI-compatible Chat endpoint，并记录：

- Prompt ID / Version / SHA-256 与完整 System/User Template；
- 生成 Answer、ReferenceToken Precision/Recall/F1 与生成耗时；
- 可选 LLM-as-a-Judge：Correctness、Completeness、Faithfulness、Relevance；
- 原有 Retrieval / Context / Hard Negative 指标，便于端到端同时分析。

示例配置：

```text
configs/experiments/qwen-java-interview-phase2-workbench.yaml
```

直接运行：

```bash
UV_CACHE_DIR=.uv-cache uv run python scripts/benchmark_chunking.py \
  --config configs/experiments/qwen-java-interview-phase2-workbench.yaml
```

启动历史对比 Workbench：

```bash
UV_CACHE_DIR=.uv-cache uv run python scripts/launch_workbench.py
```

若希望在界面中直接修改 Prompt 并执行 Dev A/B：

```bash
UV_CACHE_DIR=.uv-cache uv run python scripts/launch_workbench.py \
  --config configs/experiments/qwen-java-interview-phase2-workbench.yaml
```

Workbench 扫描 `results/raw/*.json`，可比较任意 `experiment_id + strategy` 的指标绝对值、
Delta、Delta%，并并排显示 Prompt 内容、Version 与 Hash。页面触发的实验仍统一调用
`BenchmarkRunner`，因此不能绕过冻结 Test 的 dataset hash 和一次性 execution ledger。

完整说明见 [`docs/PHASE2-WORKBENCH.md`](docs/PHASE2-WORKBENCH.md)。

## 测试

```bash
UV_CACHE_DIR=.uv-cache uv run pytest
```

Golden tests 还覆盖 span union、overlap 去重、Evidence Coverage/Recall、
AllEvidenceHit、ContextPrecision、Hard Negative、query detector/decomposer、RRF、
section diversity、context dedup/token budget 和 Test execution guard。Phase 1.5 本身仍不实现
Semantic Chunking、BM25、Hybrid、HNSW 或 LLM-as-a-Judge；LLM Judge 仅作为 Phase 2
Generation Evaluation 的可选层。