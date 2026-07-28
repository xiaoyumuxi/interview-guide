from __future__ import annotations

import random
import re
from collections import defaultdict

from rag_lab.common.text import stable_id, token_count
from rag_lab.dataset.models import Evidence, QuerySample, QueryType
from rag_lab.models import NodeType, StructuredDocument


class DatasetBuilder:
  """Evidence-first deterministic generator used when no local generation LLM is available."""

  def __init__(self, min_tokens: int = 18, max_tokens: int = 220, seed: int = 42) -> None:
    self.min_tokens = min_tokens
    self.max_tokens = max_tokens
    self._random = random.Random(seed)

  def sample_evidence(self, documents: list[StructuredDocument]) -> list[Evidence]:
    evidences: list[Evidence] = []
    for document in documents:
      for block in document.blocks:
        if block.node_type not in {
          NodeType.PARAGRAPH, NodeType.LIST, NodeType.CODE_BLOCK, NodeType.TABLE, NodeType.QUOTE,
        }:
          continue
        text = document.markdown[block.start_offset:block.end_offset]
        count = token_count(text)
        if self.min_tokens <= count <= self.max_tokens and not self._is_noise(text):
          evidences.append(Evidence(
            id=stable_id("evidence", document.document_id, block.start_offset, block.end_offset),
            document_id=document.document_id,
            heading_path=block.heading_path,
            start_offset=block.start_offset,
            end_offset=block.end_offset,
            text=text,
          ))
    return evidences

  def build(self, evidences: list[Evidence], target: int = 100) -> list[QuerySample]:
    if len(evidences) < 30:
      raise ValueError("At least 30 evidence blocks are required for a balanced dataset")
    shuffled = evidences.copy()
    self._random.shuffle(shuffled)
    target_counts = self._target_counts(target)
    samples: list[QuerySample] = []
    cursor = 0
    for query_type in (
      QueryType.DIRECT_FACT, QueryType.PARAPHRASE, QueryType.TERMINOLOGY,
      QueryType.HARD_NEGATIVE,
    ):
      for _ in range(target_counts[query_type]):
        evidence = shuffled[cursor % len(shuffled)]
        cursor += 1
        samples.append(self._single_sample(len(samples), query_type, evidence, evidences))
    for _ in range(target_counts[QueryType.MULTI_SECTION]):
      first = shuffled[cursor % len(shuffled)]
      second = shuffled[(cursor + max(1, len(shuffled) // 3)) % len(shuffled)]
      cursor += 1
      samples.append(self._multi_sample(len(samples), first, second))
    for index in range(target_counts[QueryType.UNANSWERABLE]):
      questions = [
        "Kafka KRaft Controller Quorum 如何完成领导者选举？",
        "Kubernetes 的 etcd 压缩参数如何配置？",
        "CUDA kernel 的 shared memory bank conflict 如何避免？",
        "Rust borrow checker 如何处理高阶生命周期？",
        "Apache Flink checkpoint barrier 如何对齐？",
        "ClickHouse MergeTree 的后台合并策略是什么？",
        "Istio xDS 增量推送如何保证配置一致性？",
        "OpenTelemetry Collector 如何执行 tail sampling？",
        "Linux eBPF verifier 如何证明程序一定终止？",
        "Raft joint consensus 如何安全变更成员？",
        "Elasticsearch segment merge 如何回收已删除文档？",
        "Nginx event loop 如何处理 accept mutex？",
        "WebRTC ICE candidate 如何完成连通性检查？",
        "Apache Iceberg manifest list 如何加速文件裁剪？",
        "Prometheus remote write 如何处理乱序样本？",
      ]
      samples.append(QuerySample(
        id=f"rag_{len(samples) + 1:03d}",
        question=questions[index % len(questions)],
        reference_answer="当前知识库无法回答。",
        evidences=[],
        type=QueryType.UNANSWERABLE,
        difficulty="HARD",
        answerable=False,
      ))
    return samples

  def select_balanced(self, candidates: list[QuerySample], target: int) -> list[QuerySample]:
    target_counts = self._target_counts(target)
    selected: list[QuerySample] = []
    for query_type, count in target_counts.items():
      group = [sample for sample in candidates if sample.type == query_type]
      if len(group) < count:
        raise ValueError(f"Not enough {query_type} candidates: {len(group)} < {count}")
      selected.extend(group[:count])
    return selected

  def stratified_split(
    self,
    samples: list[QuerySample],
    dev_ratio: float = 0.7,
  ) -> tuple[list[QuerySample], list[QuerySample]]:
    groups: dict[QueryType, list[QuerySample]] = defaultdict(list)
    for sample in samples:
      groups[sample.type].append(sample)
    dev: list[QuerySample] = []
    test: list[QuerySample] = []
    for group in groups.values():
      self._random.shuffle(group)
      cut = round(len(group) * dev_ratio)
      for sample in group[:cut]:
        sample.split = "dev"
        dev.append(sample)
      for sample in group[cut:]:
        sample.split = "test"
        test.append(sample)
    return sorted(dev, key=lambda item: item.id), sorted(test, key=lambda item: item.id)

  @staticmethod
  def _is_noise(text: str) -> bool:
    lowered = text.lower()
    return (
      text.count("http") > 2
      or lowered.startswith(("copyright", "目录", "table of contents"))
      or not re.search(r"[\w\u3400-\u9fff]", text)
    )

  @staticmethod
  def _target_counts(target: int) -> dict[QueryType, int]:
    weights = {
      QueryType.DIRECT_FACT: 25,
      QueryType.PARAPHRASE: 25,
      QueryType.TERMINOLOGY: 15,
      QueryType.MULTI_SECTION: 15,
      QueryType.HARD_NEGATIVE: 10,
      QueryType.UNANSWERABLE: 10,
    }
    counts = {kind: round(target * weight / 100) for kind, weight in weights.items()}
    counts[QueryType.DIRECT_FACT] += target - sum(counts.values())
    return counts

  @staticmethod
  def _heading(evidence: Evidence) -> str:
    return evidence.heading_path[-1] if evidence.heading_path else "该主题"

  def _single_sample(
    self,
    index: int,
    query_type: QueryType,
    evidence: Evidence,
    all_evidence: list[Evidence],
  ) -> QuerySample:
    heading = self._heading(evidence)
    keyword = self._keyword(evidence.text, heading)
    if query_type == QueryType.DIRECT_FACT:
      question = f"根据文档，{heading}中的 {keyword} 核心机制是什么？"
    elif query_type == QueryType.PARAPHRASE:
      question = f"实际系统涉及 {keyword} 时，文档对{heading}给出了怎样的解释或处理思路？"
    elif query_type == QueryType.TERMINOLOGY:
      question = f"术语 {keyword} 在文档中表示什么？"
    else:
      question = f"{heading}里的 {keyword} 与相邻概念相比，正确描述是什么？"
    negative_evidences = []
    if query_type == QueryType.HARD_NEGATIVE:
      negative_evidences = [
        item for item in all_evidence
        if item.id != evidence.id and set(item.heading_path[:-1]) & set(evidence.heading_path[:-1])
      ][:2]
    return QuerySample(
      id=f"rag_{index + 1:03d}",
      question=question,
      reference_answer=evidence.text,
      evidences=[evidence],
      type=query_type,
      difficulty="HARD" if query_type == QueryType.HARD_NEGATIVE else "MEDIUM",
      negative_evidence_ids=[item.id for item in negative_evidences],
      negative_evidences=negative_evidences,
    )

  def _multi_sample(self, index: int, first: Evidence, second: Evidence) -> QuerySample:
    first_heading = self._heading(first)
    second_heading = self._heading(second)
    return QuerySample(
      id=f"rag_{index + 1:03d}",
      question=f"{first_heading}和{second_heading}的机制分别是什么，二者有何区别？",
      reference_answer=f"{first.text}\n\n{second.text}",
      evidences=[first, second],
      type=QueryType.MULTI_SECTION,
      difficulty="HARD",
    )

  @staticmethod
  def _keyword(text: str, fallback: str) -> str:
    quoted = re.findall(r"`([^`]{2,80})`", text)
    if quoted:
      return quoted[0]
    candidates = re.findall(r"[A-Za-z][A-Za-z0-9_.-]{2,}", text)
    return max(candidates, key=len) if candidates else fallback
