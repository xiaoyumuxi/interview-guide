# RAG Offline Evaluation Interview Notes

以下回答基于真实 Java 八股语料的 agent-reviewed Dev 实验
`20260728T083734Z-47450`。之后 Test 经独立智能体 40/40 复核，以非人工口径冻结，
并只运行一次（`20260728T115625Z-57404`）。

## 为什么把调优从 Spring Boot 拆出去？

生产系统的事务、数据库、pgvector、接口和业务逻辑会引入额外变量。独立 Lab 固定语料、
dataset、Qwen 和 Exact Retriever，每次只替换 Chunker；验证后只迁移有效规则。

## 为什么第一阶段不用 pgvector？

Exact cosine 能给出无 ANN 误差的完整排序，不会把 Chunk 质量与 HNSW 近似误差混在一起。
先确定 Chunk，再独立评估 ANN recall 和延迟。

## 为什么 Ground Truth 用 Evidence Span？

三种 Chunker 会产生不同 Chunk ID。数据集绑定 normalized Markdown 的 document ID 和
source offsets，运行时通过 span overlap 映射到任意 Chunk。最终 135 个 gold Evidence
和 28 个负 Evidence 都通过严格 `[start,end)` 回放。

## 数据问题是否调用了 Qwen 生成？

没有。问题和简洁答案由子智能体从固定 Evidence 编写，`generator_model` 全为空。
Qwen3-Embedding-0.6B 只用于问题语义去重和检索向量化。

## 为什么需要真实来源固定？

语料来自 JavaGuide 和 advanced-java 的 48 篇原始 Markdown。URL、commit、license、
relative path 和 SHA-256 都被记录；推广、导航和纯链接页被排除，上游全文不提交。

## Fixed 与 Structure 的差异是什么？

Fixed 以 512/64 机械滑窗，可能混入相邻主题。Structure 保留 heading/section/block
边界，并把 heading path 加入 embedding text。真实 Dev 上 Structure 的 Recall@5 /
MRR 为 0.9749 / 0.9030，Fixed 为 0.9635 / 0.8832。

## Structure 是否所有指标都更好？

不是。Structure 的 Recall@1、Recall@5、MRR 更好，但 Fixed 的 Recall@3 和 Recall@10
更高；Multi-Section Recall@5 也是 Fixed 更高。选择必须绑定目标指标，不能只报有利数字。

## Parent-Child 为什么没有胜出？

它用细粒度 child 检索，再用 parent 恢复上下文，但本轮产生 5,475 个 child，索引估算
22.4 MB；Recall@5 0.8881、MRR 0.8732，都低于 Structure，当前成本收益比不成立。

## Recall、HitRate、MRR 有什么区别？

HitRate@K 判断是否至少命中一个 gold Evidence。Recall@K 是命中的 gold 数除以全部 gold
数；Multi-Section 命中一个只能获得部分 recall。MRR 关注第一个相关结果排名。

## Hard Negative 做到了什么？

每条 Hard Negative 保存一个 gold 和两个同概念簇、语义相近但不能回答问题的完整负
Evidence，并记录不成立原因。现有 Metric 按要求未修改，只测 gold retrieval，所以当前
结果不能冒充 negative exclusion rate。

## Unanswerable 为什么不计普通 Recall？

普通 dense retriever 总会返回结果，没有拒答阈值就不存在可靠 no-answer 指标。数据集
保留 10 条边界问题，但必须单独设计拒答机制后再评测。

## Dev/Test 为什么按 Evidence 连通簇切分？

仅按题型随机切分会让同一 Evidence 或同一 Section 同时出现在 Dev 和 Test。当前切分把
共享 gold/negative Evidence 或 heading section 的样本绑定到同一侧，并确保两侧都覆盖
12 类和两个来源。

## 子智能体代审是否等于人工审核？

不等于。两个审核子智能体最终分别批准 Dev 80/80 和 Test 40/40，输出状态为
`AGENT_APPROVED`；最终冻结前的独立复核为 40/40 APPROVE，53/53 Evidence
offset/provenance 回放通过。Test 标记为 `human_reviewed=false`、
`freeze_kind=AGENT_REVIEWED_NOT_HUMAN`，不能冒充人工金标。

## 当前迁移建议是什么？

冻结 Test 上 Fixed 与 Structure 的 EvidenceRecall@5/50 同为 0.9459，但 Structure
的 Coverage@5、ContextPrecision@5、MRR 和 Hard Negative 排序更好，因此推荐
Structure-Aware，同时保留 Fixed 作为更小索引的 baseline。Parent-Child 暂缓。
