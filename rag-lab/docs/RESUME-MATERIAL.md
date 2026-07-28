# Resume Material — Real Corpus Only

> 状态：**AGENT REVIEWED, NOT HUMAN-FROZEN**。本文件只引用真实 Java 八股语料结果，
> 不包含 synthetic smoke 指标。Dev 80/Test 40 已通过子智能体逐条代审，但 Test 未人工
> 冻结；以下内容不能写成“最终测试集效果”。

## 候选项目描述

搭建独立 Python RAG 离线评测框架，基于两个固定开源仓库的 48 篇真实 Java 后端
Markdown 构建 Evidence Span Ground Truth；记录 commit、license、relative path 与
SHA-256，实现严格 offset 回放、语义去重、无泄漏 Dev/Test 切分、本地 Qwen embedding、
SQLite cache、Exact Cosine Search，以及 Fixed、Structure-Aware、Parent-Child
三种 Chunk 策略对照。

在子智能体逐条代审通过的 80 条真实 Dev Query 上，Structure-Aware 相对 Fixed 将 Recall@5 从
0.9635 提升到 0.9749、MRR 从 0.8832 提升到 0.9030；当前 Parent-Child 产生 5,475 个
子 Chunk，但 Recall@5/MRR 仅为 0.8881/0.8732，因此暂不迁移该配置。

## 候选 Bullet

- 构建基于 48 篇真实 Java 后端 Markdown 的 RAG offline benchmark，以严格可回放的
  source offsets 公平评测不同 Chunk 边界，并覆盖六类 Query。
- 使用本地 Qwen3-Embedding-0.6B 与 Exact Cosine Search 隔离切块变量；在 agent-reviewed
  Dev 上，Structure-Aware 相对 Fixed 将 Recall@5 提升 1.14 个百分点、MRR 提升
  1.97 个百分点。
- 建立 Evidence/Section 分组切分门禁，使 Dev 80 与 Test 40 均覆盖 12 类及两个来源，
  gold/negative Evidence、文本和 offset 区间跨 split 零泄漏。
- 量化 Parent-Child 成本：5,475 个 child、约 22.4 MB 索引估算，且主要质量指标低于
  1,328-chunk 的 Structure-Aware，据此暂缓高成本方案。

## 使用边界

- 只能称为“真实语料 agent-reviewed Dev 结果”，不能称为最终 Test 指标。
- 不能写“人工标注/人工审核完成”；当前完成机器门禁与子智能体逐条代审。
- Test 40 全部由真实审核者批准并冻结后，才能补充最终 Test 结果。
- 不得引用 `synthetic-smoke-v1` 的任何数字。
