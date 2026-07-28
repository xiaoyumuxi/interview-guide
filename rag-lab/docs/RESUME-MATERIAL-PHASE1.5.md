# Resume Material — Phase 1.5

## 可直接使用

基于 JavaGuide 与 advanced-java 固定版本真实 Markdown 语料搭建 RAG
离线评测流水线，通过可回放 Evidence Span、区间去重、分级
Evidence Recall/Coverage、Context Precision 与 Hard Negative 排序指标，
受控比较 Fixed、Structure-Aware、Parent-Child 三种分块策略。

在 80 条 **Agent-reviewed Dev** 上，Structure-Aware 相比 Fixed 将
EvidenceRecall@5/50 从 0.9361 提升到 0.9658、ContextPrecision@5 从
0.1220 提升到 0.2085；在复用 Dev Evidence、采用更隐式复杂提问的
48 条 **Agent-reviewed-not-human Hard Query Stress Set** 上，Fixed 严格
Recall 更高（0.7812 vs 0.7118），据此保留 Fixed 回退策略，而不声称完成
独立留出泛化验证。

在方案固定后，由独立智能体复核并冻结 40 条 Test（非人工审核），仅执行一次：
Fixed 与 Structure-Aware 的 EvidenceRecall@5/50 均为 0.9459；Structure-Aware
将 EvidenceCoverage@5 从 0.9220 提升到 0.9457、MRR 从 0.7601 提升到
0.9052，并将 Hard Negative pairwise gold win rate 从 0.90 提升到 1.00。

针对多知识段问题实现纯 Query 驱动的中文规则拆分、Multi-Query Exact
Retrieval、RRF、Section Diversity 与预算化 Context Assembly；通过
S0–S3 消融发现当前这版规则 Query Decomposition + RRF 在 Multi-Section
上无收益且查询调用增加约 60%，因此未建议默认上线；该结论不外推为
“所有 Multi-Query 方法普遍无效”。

## 简短版本

搭建真实 Java 面试语料 RAG Offline Evaluation Pipeline，以 source-span
Coverage、Context Precision 和 Hard Negative margin 评测检索；实现
Query Decomposition/RRF/Diversity 消融，并用 Agent-reviewed Dev 数据识别
并否决当前高成本、无收益的规则 Query Decomposition + RRF 方案。

## 边界声明

- 数字均为本地 Qwen3-Embedding-0.6B + Exact Cosine 的 Agent-reviewed
  Dev / Hard Query Stress Set 实验；后者复用 Dev Evidence，不是独立留出集。
- Test 是 `AGENT_REVIEWED_NOT_HUMAN` 冻结集，不是人工金标；已执行一次并由账本锁定。
- Test 领域分布有意/事实上偏向网络、Redis、JVM、MySQL，更接近 Domain Shift，
  且普通检索指标只统计 37 条 answerable query。
- 不使用“最终 Recall”“线上效果”“生产 A/B”“全面提升”等表述。
