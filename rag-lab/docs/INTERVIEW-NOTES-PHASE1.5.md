# Interview Notes — Phase 1.5

## 为什么 1% overlap 不能作为正式 Recall？

它只证明 Top-K 与 Evidence 有极少字符交集，不证明答案所需内容完整。
Current Dev 的 Parent-Child `AnyOverlapRecall@5=0.8881`，但
`EvidenceRecall@5/50=0.6279`；Hard Query Dev 的差距更大（0.6354 vs 0.2882）。
兼容指标仍保留，但代码在 `evaluation/metrics.py` 中明确命名为
`AnyOverlapRecall`。

## EvidenceRecall 和 EvidenceCoverage 有什么区别？

Coverage 是每条 Evidence 被覆盖的连续比例；Recall 把 Coverage 按 25%、
50% 或 75% 门槛离散化后，统计达标 Evidence 的比例。Coverage 能显示
“差一点”，Recall 更适合设发布门槛。区间先经 `evaluation/spans.py` 合并，
不会重复累计 overlap chunks。

## 为什么需要 ContextPrecision？

只看 Recall 会奖励“返回更多文本”。ContextPrecision 把合并后的 Top-K
原始 source span 作为分母，仅 gold span 作为相关内容。Current Dev 中 Fixed
Recall@5/50 达 0.9361，但 ContextPrecision@5 只有 0.1220，说明命中之外仍有
大量噪声。

## Fixed Chunk 为什么可能 Recall 高但 ContextPrecision 低？

512/64 窗口常把 Evidence 连同相邻主题一起召回。较大的连续窗口提高覆盖概率，
同时扩大无关分母。Hard Query Dev 上 Fixed Recall 高于 Structure
（0.7812 vs 0.7118），但 precision 更低（0.1268 vs 0.1909）。

## 为什么 Heading Prefix 不能参与 Source Span 评测？

Heading Prefix 是检索提示，不在原始 Evidence offset 内。`DocumentChunk`
显式区分 `embedding_text` 和 `source_text`；coverage/precision 只读取
`document_id/start_offset/end_offset`。否则长标题会虚增相关字符或分母。

## Hard Negative 为什么不能只看 Gold Recall？

系统可能同时召回正确证据和一个语义更像、结论却错误的证据。Current Dev
Fixed 的 gold Recall 很高，但 NegativeExposure@5 为 0.4444，pairwise win
rate 只有 0.90。只看 gold 会漏掉排序歧义。

## NegativeExposure 表达什么？

它分别回答“这条 Query 是否暴露任一负证据”和“多少负 Evidence 进入
Top-K”。越低通常越好，但必须结合 GoldBeforeNegative：Hard Query Dev
Parent-Child exposure@5 为 0，却只有 0.2667 的 gold-before-negative，因为
它经常连 gold 也没召回。

## Gold-Negative Margin 有什么意义？

`best_gold_score - best_negative_score` 衡量区分余量。Hard Query Dev Fixed 的最小
margin 为 -0.0161，代表至少一条负证据分数高于 gold；Structure 的最小 margin
为 0.0184，但 pairwise win 仍只有 0.95，说明还不是完全稳健。

## Multi-Section 为什么不适合只看 MRR？

MRR 只看第一个相关 Chunk。一个三段问题即使第一段排第 1，另外两段缺失，
MRR 仍可能很好。Phase 1.5 主看 `EvidenceCoverage`、`EvidenceRecall@5/50`
和 `AllEvidenceHit@5/50`。Current Dev Multi-Section S0 的 AllHit 只有
0.5833，这比首个命中更能说明完整性。

## Query Decomposition 如何避免读取 Gold？

`retrieval/multi_query.py` 的 detector/decomposer API 只接收一个 `str`。
它用“分别、区别、A 而 B、三元列表”等确定性规则，不能访问 `QuerySample`、
type、answer 或 evidence。`test_no_gold_leakage_multi_query_api_only_uses_question`
验证调用边界。

## 为什么使用 RRF 而不是直接合并 Cosine Score？

不同子问题的 cosine 分布不一定同尺度。RRF 只组合每路排名：
`sum(1/(60+rank))`，避免把不可校准的分数直接相加，并保留每路
`source_query/source_rank/dense_score` 调试轨迹。

## Section Diversity 解决什么问题？

它限制同一 `(document_id, heading_path)` 在最终 Top-K 的数量，避免多路检索
被一个 Section 的相邻 chunks 占满。此次 S2 与 S1 主指标相同，说明当前失败
并非主要由同 Section 重复造成，因此不能声称它有效。

## Context Expansion 为什么不能冒充 Retrieval 提升？

S3 复用 S2 ranking，新增 neighbor/section spans 只进入 context metrics。
Hard Query Dev coverage 从 0.7123 升到 0.8025，但 precision 从 0.1977 降到
0.1141，平均 2,826 个 lexical approximate tokens / 2,341 个 Qwen tokens。
这是以噪声和 token 换 coverage，不是 retriever
变强。

## 为什么 Test 只执行一次？

Phase 1.5 调参期间，40 条 Test 只是 agent-reviewed candidate，runner 一直拒绝
Test 路径。方案停止优化后，用户授权独立智能体复核并以
`AGENT_REVIEWED_NOT_HUMAN` 冻结；随后通过专用入口执行一次。执行账本已经落盘，
runner 会拒绝第二次运行，避免根据 Test 结果继续选参。

## 当前 Test 为什么更像 Domain Shift？

Test 集中在 network(11)、Redis(9)、JVM(7)、MySQL(5)，而 Dev 集中在
JUC(18)、collections(14)、OS(10)、system design(10)。Section/evidence
泄漏为 0，但领域分布明显不同，详见 `docs/SPLIT-AUDIT.md`。

## 哪些结果证明方案不值得上线？

当前 Multi-Query 在 Current Dev Multi-Section 将 AllHit@5 从 0.5833 降到
0.3333，在 Hard Query Dev Multi-Section 无提升，同时查询 embedding/call 增约
60%。Context expansion 又显著降低 precision。因此两者都不满足事先定义的
质量与成本门槛；诚实的结论是拒绝默认上线，而不是继续调参把 Dev 做高。

Dev 与消融数字来自：

- `results/raw/20260728T092752Z-49193.json`
- `results/raw/20260728T095847Z-52944.json`
- `results/raw/20260728T100028Z-multisection-ablation.json`

冻结 Test 实验为 `results/raw/20260728T115625Z-57404.json`，状态为
**EXECUTED ONCE AND LOCKED**。它不是人工审核金标。

## Hard Query Dev 的评估边界是什么？

它复用 Current Dev Evidence Pool，只把问题改成更隐式、场景化或需要多段推理的
表达，用于测量 Query Difficulty 和 Retrieval Robustness。它没有引入新文档或
新主题，因此不能解释为独立留出评估或新领域泛化结果。

## Token 口径如何解释？

Chunk boundary 仍由 Phase 1 的 `LexicalApproxTokenizer` 决定，以保证质量实验不变。
审计只对已有 Chunk/Context 重新计数：Fixed 平均为 499.1 approximate tokens，
对应 439.5 Qwen tokens；两套数值分别带 `approx_` 和 `qwen_` 前缀。真实
Tokenizer 缺失时只允许离线 fallback，并记录 `token_count_mode=approximate`。
