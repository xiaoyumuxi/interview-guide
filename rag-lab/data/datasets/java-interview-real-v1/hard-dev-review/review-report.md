# Hard Dev 独立代理审核报告

> Release update: 本文件保留首次审核的 36/48 通过、12 条 REJECT 记录。
> 被拒样本修复后，第二个独立上下文通过 10 条并再次拒绝 2 条，第三个独立
> 上下文最终通过剩余 2 条。最终 `final-decisions.jsonl` 为 48/48 APPROVE，
> 发布状态是 `AGENT_REVIEWED_NOT_HUMAN`，不是人工审核。完整复审轨迹见
> `rereview-report.md` 与 `final-rereview-report.md`。

## 结论

- 审核对象：`hard-dev-draft.jsonl`
- 审核条数：48
- 通过：36
- 拒绝：12
- 审核身份：`hard_dev_reviewer`
- 审核性质：`AGENT_REVIEWED_NOT_HUMAN`，独立子智能体审核，不是人工审核
- Test 使用边界：仅进行只读泄漏审计；未执行检索、embedding、参数选择或 Benchmark

本轮是首次审核。发现不合格项后均按要求直接 `REJECT`，没有修改草稿样本。逐条结构化决定见 `review-decisions.jsonl`。

## 审核方法

逐条阅读了问题、Reference Answer、全部 Gold Evidence 和 Hard Negative Evidence，检查：

- 问题是否像真实 Java 后端面试追问，且没有照抄 Heading 或堆砌答案关键词；
- Reference Answer 的每个技术断言是否能由 Gold Evidence 直接支撑；
- Gold Evidence 是否必要、无重复或无关 Span；
- Hard Negative 是否来自同一概念簇、语义相近但不能正确支持答案；
- Multi-Section 样本是否确实依赖两个或以上具有逻辑关系的真实 Section；
- Evidence 是否能按 `document_id + [start_offset, end_offset)` 从规范化 Markdown 原文逐字回放；
- 是否与 Test 存在 Evidence hash、Section、Span、答案或问题近似改写泄漏。

自动校验结果为 48 条 offset 回放全部通过，Test Evidence hash/Section/Span 重叠为 0，Reference Answer 直接复用为 0，问题近似改写为 0。Test 状态始终为 `NOT EXECUTED`。

## 拒绝项

### Hard Negative 不合格

- `hard_dev_009`：AQS 资源共享方式负证据也说明自定义同步器实现模板方法，部分支持答案，形成 Gold/Negative 标签冲突。
- `hard_dev_025`、`hard_dev_026`、`hard_dev_027`：Redis 线程模型与过期字典/过期删除只是同属 Redis 大类，不是同一语义概念簇。
- `hard_dev_029`、`hard_dev_030`：SACK/累计确认与三次挥手不是同一语义概念簇。
- `hard_dev_031`、`hard_dev_032`：连接关闭与 SACK 丢包重传不是同一语义概念簇。
- `hard_dev_037`：XA/TCC/Saga 与 Redis 分布式锁仅共享“分布式”上位词，负样本过于随机。
- `hard_dev_046`：负证据明确包含空值缓存和布隆过滤器，直接支持答案中的穿透治理，不能标为负证据。

### Multi-Section 关系不成立

- `hard_dev_025`：`type=MULTI_SECTION`，但只有一个 Gold Evidence。
- `hard_dev_032`：`type=MULTI_SECTION`，但只有一个关闭握手 Section；问题中的多个条件仍由同一 Span 完整回答。

### Gold Evidence 不唯一

- `hard_dev_033`：`evidence_7702c88b1e0322ac` 已完整回答返回后为何仍需 O(N) 扫描；第二条 Gold 只讨论 fd 上限、位图复制和重建，与该问题和答案没有不可替代关系。

### 难度不足

- `hard_dev_007`：仅由“去重”和“按键查值”直译为 Set/Map，低于困难 Dev 预期；其负证据也是泛化的集合优点介绍，缺少同一选型问题中的语义迷惑性。

## 通过项

`hard_dev_001`、`hard_dev_002`、`hard_dev_003`、`hard_dev_004`、`hard_dev_005`、`hard_dev_006`、`hard_dev_008`、`hard_dev_010`、`hard_dev_011`、`hard_dev_012`、`hard_dev_013`、`hard_dev_014`、`hard_dev_015`、`hard_dev_016`、`hard_dev_017`、`hard_dev_018`、`hard_dev_019`、`hard_dev_020`、`hard_dev_021`、`hard_dev_022`、`hard_dev_023`、`hard_dev_024`、`hard_dev_028`、`hard_dev_034`、`hard_dev_035`、`hard_dev_036`、`hard_dev_038`、`hard_dev_039`、`hard_dev_040`、`hard_dev_041`、`hard_dev_042`、`hard_dev_043`、`hard_dev_044`、`hard_dev_045`、`hard_dev_047`、`hard_dev_048`。

## 复审要求

拒绝项应由作者上下文修复，之后必须交给另一个独立审核上下文复审。复审仍应标记 `AGENT_REVIEWED_NOT_HUMAN`，不得称为人工审核或冻结数据。
