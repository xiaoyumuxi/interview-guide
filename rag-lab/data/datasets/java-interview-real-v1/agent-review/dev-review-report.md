# java-interview-real-v1 Dev 代理审核报告

## 结论

- 审核对象：`dev-pending-review.jsonl`
- 审核条数：80
- 通过：80
- 拒绝：0
- 审核身份：`dev_release_reviewer`
- 审核性质：独立子智能体审核，不是人工审核
- 模型调用：未调用外部或本地生成模型，也未调用 embedding 模型

本次审核没有修改源 JSONL 或项目代码。逐条决定记录在 `dev-decisions.jsonl`。

## 全量机械校验

- 80 个 sample ID 唯一，全部属于 `dev` split。
- 类型分布：Terminology 12、Paraphrase 19、Direct Fact 21、Unanswerable 7、Multi Section 12、Hard Negative 9。
- 所有正 Evidence 与负 Evidence 均按 `rag_lab_normalized_markdown_v1` 的 `[start_offset, end_offset)` 严格回放，失败数为 0。
- 所有 support quotes 均可在对应正 Evidence 中逐字定位，失败数为 0。
- 使用到的 27 篇文档，其 repository、URL、commit、license、relative path、file SHA-256、document ID、category 和 offset basis 均与 corpus manifest 一致。
- 27 篇文档的 `raw.md` SHA-256 均与 manifest 中的 `file_sha256` 一致。
- Answerable、Unanswerable、Hard Negative 的结构约束均通过。

## 修复项复审

### `java_real_candidate_071` — Pass

问题与答案已明确限定为“直接访问成员”。答案不再绝对声称静态方法无法访问实例成员，并补充说明：获得对象引用后，静态方法可以通过该对象访问实例成员。Evidence offset 与 support quotes 均重新回放通过。

### `java_real_candidate_177` — Pass

两条 Hard Negative 已改为“用户线程、内核线程和线程模型”以及“纤程、协程和虚拟线程”Section。它们与目标问题同属线程概念簇，但不再列出同进程线程的共享资源或私有执行现场，单独或组合均不能回答目标问题。正负 Evidence offset、support quotes 和 negative IDs 均重新校验通过。

### `java_real_candidate_178` — Pass

第二条 Hard Negative 已改为 epoll 的 LT/ET 触发语义。第一条 poll Evidence 是相邻对照，但不包含 select 的用户态/内核态位图复制机制；新的 LT/ET Evidence 也不回答 fd 集合传递或 O(N) 就绪查找。两条负证据组合后仍不足以完整回答目标问题。正负 Evidence offset、support quotes 和 negative IDs 均重新校验通过。

## 通过项

`java_real_candidate_001`、`002`、`003`、`004`、`005`、`006`、`009`、`013`、`016`、`020`、`022`、`024`、`026`、`027`、`028`、`029`、`031`、`032`、`035`、`036`、`037`、`038`、`039`、`040`、`042`、`043`、`044`、`045`、`049`、`051`、`060`、`066`、`069`、`070`、`071`、`079`、`080`、`081`、`083`、`088`、`089`、`090`、`096`、`097`、`100`、`101`、`103`、`106`、`107`、`111`、`112`、`115`、`116`、`117`、`118`、`121`、`122`、`124`、`125`、`131`、`132`、`140`、`141`、`143`、`147`、`148`、`151`、`152`、`153`、`154`、`155`、`157`、`158`、`167`、`174`、`175`、`177`、`178`、`179`、`180`。

其中 7 条 Unanswerable 均通过全语料关键词与主题检查：相关产品名偶有泛泛提及的，也没有足以回答目标机制的正文证据。

## 发布建议

当前 80 条均已通过代理审核，可进入后续 Dev 发布流程。任何最终文件都应继续保留“代理审核”标识，不应称为人工审核或冻结数据。
