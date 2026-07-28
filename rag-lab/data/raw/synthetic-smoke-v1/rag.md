# Rag 工程笔记

## Evidence Span

Evidence Span的第一项机制围绕 `source-offset` 展开。系统先识别请求的边界与状态，再用 source-offset 保存能够复核的中间信息；这一过程强调确定性、可观测性和失败后恢复，避免把隐含状态散落到调用链中。编号 D1-A 用于区分本段事实。

Evidence Span的第二项机制使用 `ground-truth` 处理异常路径。实现会记录输入、决策和最终结果，并在重复请求到达时依据 ground-truth 保持一致行为；容量达到阈值后应显式降级，而不是静默丢弃数据。编号 D1-B 用于区分这一证据。

## Exact Cosine Search

Exact Cosine Search的第一项机制围绕 `dot-product` 展开。系统先识别请求的边界与状态，再用 dot-product 保存能够复核的中间信息；这一过程强调确定性、可观测性和失败后恢复，避免把隐含状态散落到调用链中。编号 D2-A 用于区分本段事实。

Exact Cosine Search的第二项机制使用 `L2-normalization` 处理异常路径。实现会记录输入、决策和最终结果，并在重复请求到达时依据 L2-normalization 保持一致行为；容量达到阈值后应显式降级，而不是静默丢弃数据。编号 D2-B 用于区分这一证据。

## Embedding Cache

Embedding Cache的第一项机制围绕 `SHA-256` 展开。系统先识别请求的边界与状态，再用 SHA-256 保存能够复核的中间信息；这一过程强调确定性、可观测性和失败后恢复，避免把隐含状态散落到调用链中。编号 D3-A 用于区分本段事实。

Embedding Cache的第二项机制使用 `cache-key` 处理异常路径。实现会记录输入、决策和最终结果，并在重复请求到达时依据 cache-key 保持一致行为；容量达到阈值后应显式降级，而不是静默丢弃数据。编号 D3-B 用于区分这一证据。

## Structure Chunking

Structure Chunking的第一项机制围绕 `heading-path` 展开。系统先识别请求的边界与状态，再用 heading-path 保存能够复核的中间信息；这一过程强调确定性、可观测性和失败后恢复，避免把隐含状态散落到调用链中。编号 D4-A 用于区分本段事实。

Structure Chunking的第二项机制使用 `Markdown-AST` 处理异常路径。实现会记录输入、决策和最终结果，并在重复请求到达时依据 Markdown-AST 保持一致行为；容量达到阈值后应显式降级，而不是静默丢弃数据。编号 D4-B 用于区分这一证据。

## Parent Child Retrieval

Parent Child Retrieval的第一项机制围绕 `child-index` 展开。系统先识别请求的边界与状态，再用 child-index 保存能够复核的中间信息；这一过程强调确定性、可观测性和失败后恢复，避免把隐含状态散落到调用链中。编号 D5-A 用于区分本段事实。

Parent Child Retrieval的第二项机制使用 `parent-expansion` 处理异常路径。实现会记录输入、决策和最终结果，并在重复请求到达时依据 parent-expansion 保持一致行为；容量达到阈值后应显式降级，而不是静默丢弃数据。编号 D5-B 用于区分这一证据。
