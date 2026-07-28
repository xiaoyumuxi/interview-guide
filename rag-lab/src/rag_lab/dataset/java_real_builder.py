from __future__ import annotations

import random
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

import numpy as np

from rag_lab.chunking.structure import StructureAwareChunker
from rag_lab.common.text import normalize_for_hash, stable_id, token_count
from rag_lab.dataset.models import Evidence, QuerySample, QueryType
from rag_lab.models import NodeType, StructuredDocument

NOISE_HEADINGS = (
  "参考资料", "参考链接", "推荐阅读", "相关阅读", "扩展阅读", "公众号",
  "学习路线", "广告", "联系作者", "知识星球", "项目地址", "star",
)
NOISE_TEXT = (
  "扫码关注", "关注公众号", "知识星球", "guide哥", "点击下方", "推荐阅读",
  "本文已收录", "欢迎关注", "github star", "原创不易",
)
QUESTION_START = (
  "什么", "为什么", "为何", "如何", "怎么", "哪些", "说说", "谈谈", "解释",
  "简述", "比较", "请问", "能否", "是否", "你知道", "介绍一下", "聊聊", "什么时候",
)


@dataclass(frozen=True)
class MultiRelation:
  name: str
  left_terms: tuple[str, ...]
  right_terms: tuple[str, ...]
  questions: tuple[str, ...]


MULTI_RELATIONS = [
  MultiRelation(
    "synchronized-vs-reentrantlock",
    ("synchronized",),
    ("reentrantlock",),
    (
      "synchronized 和 ReentrantLock 在锁的使用方式与能力上有什么区别？",
      "如果业务需要可中断或公平锁，synchronized 和 ReentrantLock 应该怎么选？",
      "synchronized 自动释放锁与 ReentrantLock 手动释放锁分别意味着什么？",
    ),
  ),
  MultiRelation(
    "g1-vs-cms",
    ("g1",),
    ("cms",),
    (
      "G1 和 CMS 的内存布局与回收目标有什么差异？",
      "CMS 与 G1 分别如何控制垃圾回收停顿？",
      "从回收过程看，G1 相比 CMS 解决了哪些问题？",
    ),
  ),
  MultiRelation(
    "rdb-vs-aof",
    ("rdb",),
    ("aof",),
    (
      "Redis 的 RDB 和 AOF 在数据恢复与持久化开销上如何取舍？",
      "RDB 快照和 AOF 命令日志分别是怎样记录数据的？",
      "什么场景更适合 RDB，什么场景更适合 AOF？",
    ),
  ),
  MultiRelation(
    "cache-failures",
    ("缓存击穿",),
    ("缓存穿透", "缓存雪崩"),
    (
      "缓存击穿和缓存穿透的触发条件有什么区别？",
      "缓存击穿与缓存雪崩影响的 key 范围有什么不同？",
      "缓存穿透、缓存击穿和缓存雪崩分别应该如何识别？",
    ),
  ),
  MultiRelation(
    "optimistic-vs-pessimistic-lock",
    ("乐观锁",),
    ("悲观锁",),
    (
      "乐观锁和悲观锁对并发冲突的假设有什么不同？",
      "高冲突和低冲突场景下，乐观锁与悲观锁应该怎么选择？",
    ),
  ),
  MultiRelation(
    "http11-vs-http2",
    ("http/1.1", "http1.1"),
    ("http/2", "http2"),
    (
      "HTTP/1.1 和 HTTP/2 在连接复用方式上有什么区别？",
      "HTTP/2 的多路复用相对 HTTP/1.1 解决了什么问题？",
      "从报文传输方式看，HTTP/1.1 与 HTTP/2 有哪些核心差异？",
    ),
  ),
  MultiRelation(
    "hashmap-vs-concurrenthashmap",
    ("hashmap",),
    ("concurrenthashmap",),
    (
      "HashMap 和 ConcurrentHashMap 在线程安全与实现机制上有什么区别？",
      "并发读写场景为什么通常不用 HashMap 而选择 ConcurrentHashMap？",
      "HashMap 与 ConcurrentHashMap 对并发修改的处理方式有何不同？",
    ),
  ),
  MultiRelation(
    "process-vs-thread",
    ("进程",),
    ("线程",),
    (
      "进程和线程在资源拥有与调度单位上有什么区别？",
      "线程相对进程为什么更轻量，它们分别共享和独占哪些资源？",
    ),
  ),
  MultiRelation(
    "mvcc-vs-lock",
    ("mvcc",),
    ("锁", "lock"),
    ("MVCC 和加锁分别如何处理数据库并发读写？",),
  ),
  MultiRelation(
    "redis-cluster-vs-sentinel",
    ("cluster", "集群"),
    ("哨兵", "主从"),
    (
      "Redis Cluster 和哨兵模式解决的问题有什么不同？",
      "需要数据分片时，Redis 主从/哨兵与 Cluster 应该如何选择？",
    ),
  ),
]

HARD_GROUPS = [
  ("reentrantlock", ("reentrantlock",), ("synchronized", "aqs")),
  ("synchronized", ("synchronized",), ("reentrantlock", "aqs")),
  ("g1", ("g1",), ("cms",)),
  ("cms", ("cms",), ("g1",)),
  ("rdb", ("rdb",), ("aof",)),
  ("aof", ("aof",), ("rdb",)),
  ("cache-penetration", ("缓存穿透",), ("缓存击穿", "缓存雪崩")),
  ("cache-breakdown", ("缓存击穿",), ("缓存穿透", "缓存雪崩")),
  ("optimistic-lock", ("乐观锁",), ("悲观锁", "mvcc")),
  ("pessimistic-lock", ("悲观锁",), ("乐观锁", "mvcc")),
  ("http2", ("http/2", "http2"), ("http/1.1", "http1.1")),
  ("hashmap", ("hashmap",), ("concurrenthashmap", "hashtable")),
  ("concurrenthashmap", ("concurrenthashmap",), ("hashmap", "hashtable")),
  ("process", ("进程",), ("线程",)),
  ("thread", ("线程",), ("进程",)),
  ("mvcc", ("mvcc",), ("锁", "隔离级别")),
  ("spring-aop", ("aop",), ("ioc", "自动装配")),
  ("spring-ioc", ("ioc",), ("aop", "事务")),
  ("kafka", ("kafka",), ("消息队列", "重复消费")),
  ("distributed-lock", ("分布式锁",), ("分布式事务", "分布式 id")),
]

UNANSWERABLE_QUESTIONS = [
  "GraalVM Native Image 在 closed-world analysis 阶段如何处理反射配置？",
  "Kubernetes 的 CFS CPU throttling 为什么会造成 Java 服务尾延迟？",
  "Apache Flink 的 unaligned checkpoint 如何处理反压？",
  "ClickHouse MergeTree 的 parts 合并策略如何影响写放大？",
  "Linux eBPF verifier 如何证明循环能够终止？",
  "Project Loom 的 ScopedValue 与 ThreadLocal 在继承语义上有什么区别？",
  "Pulsar BookKeeper 的 ensemble、write quorum 和 ack quorum 如何协作？",
  "Istio ambient mesh 中 ztunnel 的数据面职责是什么？",
  "Raft joint consensus 如何保证成员变更期间的安全性？",
  "WebRTC ICE restart 会在什么情况下重新收集 candidate？",
  "Apache Iceberg 的 position delete 与 equality delete 有什么差别？",
  "ZGC 的 generational mode 如何维护跨代引用？",
  "io_uring 的 SQPOLL 模式会带来哪些 CPU 与延迟权衡？",
  "OpenTelemetry tail sampling 为什么必须在 trace 聚合后决策？",
  "Kafka KRaft 的 controller quorum 如何完成 leader election？",
]

CANDIDATE_TYPE_COUNTS = {
  QueryType.DIRECT_FACT: 50,
  QueryType.PARAPHRASE: 40,
  QueryType.TERMINOLOGY: 25,
  QueryType.MULTI_SECTION: 25,
  QueryType.HARD_NEGATIVE: 25,
  QueryType.UNANSWERABLE: 15,
}

FINAL_TYPE_COUNTS = {
  QueryType.DIRECT_FACT: 32,
  QueryType.PARAPHRASE: 28,
  QueryType.TERMINOLOGY: 18,
  QueryType.MULTI_SECTION: 18,
  QueryType.HARD_NEGATIVE: 14,
  QueryType.UNANSWERABLE: 10,
}

DEV_TYPE_COUNTS = {
  QueryType.DIRECT_FACT: 21,
  QueryType.PARAPHRASE: 19,
  QueryType.TERMINOLOGY: 12,
  QueryType.MULTI_SECTION: 12,
  QueryType.HARD_NEGATIVE: 9,
  QueryType.UNANSWERABLE: 7,
}


class SectionEvidenceSampler:
  def __init__(self, min_tokens: int = 35, max_tokens: int = 420) -> None:
    self.min_tokens = min_tokens
    self.max_tokens = max_tokens

  def sample(
    self,
    documents: list[StructuredDocument],
    source_metadata: dict[str, dict[str, Any]],
  ) -> list[Evidence]:
    evidences: list[Evidence] = []
    for document in documents:
      metadata = source_metadata.get(document.document_id)
      if metadata is None:
        continue
      for section in StructureAwareChunker._sections(document):
        if not section.heading_path or not section.blocks:
          continue
        if self._is_noise_heading(section.heading_path[-1]):
          continue
        blocks = [
          block for block in section.blocks
          if block.node_type in {
            NodeType.PARAGRAPH, NodeType.LIST, NodeType.CODE_BLOCK,
            NodeType.TABLE, NodeType.QUOTE,
          }
        ]
        for group in self._groups(blocks):
          start, end = group[0].start_offset, group[-1].end_offset
          text = document.markdown[start:end]
          if self._valid_text(text):
            evidences.append(Evidence(
              id=stable_id("evidence", document.document_id, start, end),
              document_id=document.document_id,
              heading_path=section.heading_path,
              start_offset=start,
              end_offset=end,
              text=text,
              metadata=metadata,
            ))
    return evidences

  def _groups(self, blocks: list[Any]) -> list[list[Any]]:
    groups, pending, pending_tokens = [], [], 0
    for block in blocks:
      count = token_count(block.text)
      if count > self.max_tokens:
        if pending:
          groups.append(pending)
          pending, pending_tokens = [], 0
        continue
      if pending and pending_tokens + count > self.max_tokens:
        groups.append(pending)
        pending, pending_tokens = [block], count
      else:
        pending.append(block)
        pending_tokens += count
    if pending:
      groups.append(pending)
    return groups

  def _valid_text(self, text: str) -> bool:
    count, lowered = token_count(text), text.casefold()
    if not self.min_tokens <= count <= self.max_tokens:
      return False
    if any(term in lowered for term in NOISE_TEXT):
      return False
    if len(re.findall(r"!?\[[^\]]*]\([^)]+\)", text)) > 3 or text.count("http") > 3:
      return False
    return len(re.sub(r"[`#>*|_~\-\s]", "", text)) >= 60

  @staticmethod
  def _is_noise_heading(heading: str) -> bool:
    lowered = heading.strip().casefold()
    return not lowered or any(term in lowered for term in NOISE_HEADINGS)


def build_candidates(evidences: list[Evidence], seed: int = 42) -> list[QuerySample]:
  randomizer = random.Random(seed)
  question_evidence = _unique_natural_questions(evidences)
  randomizer.shuffle(question_evidence)
  used_evidence: set[str] = set()
  candidates: list[QuerySample] = []
  for query_type in (
    QueryType.DIRECT_FACT, QueryType.PARAPHRASE, QueryType.TERMINOLOGY,
  ):
    pool = [
      (question, evidence) for question, evidence in question_evidence
      if classify_question(question) == query_type and evidence.id not in used_evidence
    ]
    selected = _balanced_by_category(pool, CANDIDATE_TYPE_COUNTS[query_type])
    for question, evidence in selected:
      sample = _single_sample(len(candidates), query_type, question, evidence)
      if sample:
        candidates.append(sample)
        used_evidence.add(evidence.id)
  candidates.extend(_multi_samples(len(candidates), evidences))
  used_questions = {normalize_for_hash(sample.question) for sample in candidates}
  candidates.extend(_hard_negative_samples(len(candidates), evidences, used_questions))
  for question in UNANSWERABLE_QUESTIONS:
    candidates.append(QuerySample(
      id=f"java_real_candidate_{len(candidates) + 1:03d}",
      question=question,
      reference_answer="当前语料没有足够证据回答该问题。",
      evidences=[],
      type=QueryType.UNANSWERABLE,
      difficulty="HARD",
      answerable=False,
      review_status="AUTO_VALIDATED",
      validation={"origin": "CURATED_UNANSWERABLE", "grounding": "NO_EVIDENCE_EXPECTED"},
    ))
  counts = defaultdict(int)
  for sample in candidates:
    counts[sample.type] += 1
  if dict(counts) != CANDIDATE_TYPE_COUNTS:
    raise ValueError(f"Candidate distribution mismatch: {dict(counts)}")
  return candidates


def _unique_natural_questions(evidences: list[Evidence]) -> list[tuple[str, Evidence]]:
  output, seen = [], set()
  for evidence in evidences:
    question = clean_heading(evidence.heading_path[-1])
    key = (evidence.document_id, tuple(evidence.heading_path))
    if key in seen or not is_natural_question(question):
      continue
    summary = extractive_summary(evidence.text, question, max_sentences=2)
    if summary is None:
      continue
    seen.add(key)
    output.append((question, evidence))
  return output


def clean_heading(heading: str) -> str:
  value = re.sub(r"^\s*\d+(?:\.\d+)*[.、)]?\s*", "", heading).strip()
  value = re.sub(r"\s*#+\s*$", "", value).strip()
  if (
    value
    and value.startswith(QUESTION_START)
    and not value.endswith(("？", "?", "。", "！", "!"))
  ):
    value += "？"
  return value


def is_natural_question(question: str) -> bool:
  stripped = question.rstrip("？?。！!").strip()
  return (
    6 <= len(stripped) <= 100
    and ("？" in question or "?" in question or stripped.startswith(QUESTION_START))
    and not any(term in stripped.casefold() for term in NOISE_HEADINGS)
  )


def classify_question(question: str) -> QueryType:
  value = question.casefold()
  if re.search(r"[A-Z]{2,}|[a-z]+(?:[A-Z][A-Za-z]+)+|`", question) or any(
    term in value for term in ("是什么", "代表什么", "作用", "含义")
  ):
    return QueryType.TERMINOLOGY
  if any(term in value for term in (
    "为什么", "为何", "如何", "怎么", "区别", "关系", "场景", "哪些", "优点",
    "缺点", "解决", "影响",
  )):
    return QueryType.PARAPHRASE
  return QueryType.DIRECT_FACT


def extractive_summary(
  evidence_text: str,
  question: str,
  max_sentences: int,
) -> tuple[str, list[str]] | None:
  parts = [
    part.strip()
    for part in re.split(r"(?<=[。！？!?；;])|\n+", evidence_text)
    if part.strip()
  ]
  candidates = []
  question_terms = set(re.findall(r"[A-Za-z0-9_.:/+-]+|[\u4e00-\u9fff]{2,}", question))
  for index, original in enumerate(parts):
    if original.startswith(("```", "~~~", "#", "![")):
      continue
    cleaned = _strip_markdown(original)
    if not 15 <= len(cleaned) <= 220 or cleaned.endswith(("？", "?")):
      continue
    overlap = sum(term.casefold() in cleaned.casefold() for term in question_terms)
    score = overlap * 5 - index * 0.03 + min(len(cleaned), 120) / 120
    candidates.append((score, index, original, cleaned))
  if not candidates:
    return None
  chosen = sorted(candidates, reverse=True)[:max_sentences]
  chosen.sort(key=lambda item: item[1])
  answer = "".join(item[3] for item in chosen)
  quotes = [item[2] for item in chosen]
  if normalize_for_hash(answer) == normalize_for_hash(_strip_markdown(evidence_text)):
    return None
  return answer, quotes


def _strip_markdown(value: str) -> str:
  text = re.sub(r"^\s*(?:[-*+]|\d+[.)])\s+", "", value)
  text = re.sub(r"!\[[^\]]*]\([^)]+\)", "", text)
  text = re.sub(r"\[([^\]]+)]\([^)]+\)", r"\1", text)
  text = re.sub(r"[`*_~]", "", text)
  return re.sub(r"\s+", " ", text).strip()


def _balanced_by_category(
  pool: list[tuple[str, Evidence]],
  count: int,
) -> list[tuple[str, Evidence]]:
  groups: dict[str, list[tuple[str, Evidence]]] = defaultdict(list)
  for item in pool:
    groups[item[1].metadata["category"]].append(item)
  output = []
  while len(output) < count:
    progressed = False
    for category in sorted(groups):
      if groups[category]:
        output.append(groups[category].pop())
        progressed = True
        if len(output) == count:
          break
    if not progressed:
      raise ValueError(f"Only {len(output)}/{count} balanced natural questions available")
  return output


def _single_sample(
  index: int,
  query_type: QueryType,
  question: str,
  evidence: Evidence,
) -> QuerySample | None:
  summary = extractive_summary(evidence.text, question, max_sentences=2)
  if summary is None:
    return None
  answer, support_quotes = summary
  return QuerySample(
    id=f"java_real_candidate_{index + 1:03d}",
    question=question,
    reference_answer=answer,
    evidences=[evidence],
    type=query_type,
    difficulty="MEDIUM",
    review_status="AUTO_VALIDATED",
    validation={
      "origin": "UPSTREAM_MARKDOWN_HEADING",
      "grounding": "EXTRACTIVE",
      "support_quotes": support_quotes,
    },
  )


def _multi_samples(start: int, evidences: list[Evidence]) -> list[QuerySample]:
  output = []
  for relation in MULTI_RELATIONS:
    left, right = _matching(evidences, relation.left_terms), _matching(evidences, relation.right_terms)
    if not left or not right:
      raise ValueError(f"Missing evidence for multi relation {relation.name}")
    for offset, question in enumerate(relation.questions):
      first, second = left[offset % len(left)], right[-(offset % len(right) + 1)]
      if first.id == second.id:
        second = right[(offset + 1) % len(right)]
      first_summary = extractive_summary(first.text, question, 1)
      second_summary = extractive_summary(second.text, question, 1)
      if first_summary is None or second_summary is None:
        continue
      output.append(QuerySample(
        id=f"java_real_candidate_{start + len(output) + 1:03d}",
        question=question,
        reference_answer=(
          f"{first.heading_path[-1]}：{first_summary[0]}"
          f"{second.heading_path[-1]}：{second_summary[0]}"
        ),
        evidences=[first, second],
        type=QueryType.MULTI_SECTION,
        difficulty="HARD",
        review_status="AUTO_VALIDATED",
        validation={
          "origin": "CURATED_LOGICAL_RELATION",
          "relation": relation.name,
          "grounding": "EXTRACTIVE",
          "support_quotes": [first_summary[1], second_summary[1]],
        },
      ))
  if len(output) != 25:
    raise ValueError(f"Expected 25 multi-section samples, got {len(output)}")
  return output


def _hard_negative_samples(
  start: int,
  evidences: list[Evidence],
  used_questions: set[str],
) -> list[QuerySample]:
  output = []
  for cluster, gold_terms, negative_terms in HARD_GROUPS:
    gold_pool = [
      evidence for evidence in _matching(evidences, gold_terms)
      if is_natural_question(clean_heading(evidence.heading_path[-1]))
      and normalize_for_hash(clean_heading(evidence.heading_path[-1])) not in used_questions
    ]
    negatives = _matching(evidences, negative_terms)
    for gold in gold_pool[:2]:
      question = clean_heading(gold.heading_path[-1])
      summary = extractive_summary(gold.text, question, 2)
      negative_choices = [
        item for item in negatives
        if item.id != gold.id and not any(
          term.casefold() in f"{' '.join(item.heading_path)} {item.text}".casefold()
          for term in gold_terms
        )
      ][:2]
      if summary is None or len(negative_choices) < 2:
        continue
      output.append(QuerySample(
        id=f"java_real_candidate_{start + len(output) + 1:03d}",
        question=question,
        reference_answer=summary[0],
        evidences=[gold],
        type=QueryType.HARD_NEGATIVE,
        difficulty="HARD",
        negative_evidence_ids=[item.id for item in negative_choices],
        negative_evidences=negative_choices,
        review_status="AUTO_VALIDATED",
        validation={
          "origin": "UPSTREAM_HEADING_WITH_CONCEPT_CLUSTER_NEGATIVES",
          "cluster": cluster,
          "grounding": "EXTRACTIVE",
          "support_quotes": summary[1],
        },
      ))
      used_questions.add(normalize_for_hash(question))
      if len(output) == 25:
        return output
  raise ValueError(f"Expected 25 hard-negative samples, got {len(output)}")


def _matching(evidences: list[Evidence], terms: tuple[str, ...]) -> list[Evidence]:
  scored = []
  for evidence in evidences:
    value = f"{' '.join(evidence.heading_path)}\n{evidence.text}".casefold()
    score = sum(value.count(term.casefold()) for term in terms)
    if score:
      scored.append((score, evidence))
  return [
    evidence for _, evidence in sorted(
      scored, key=lambda item: (-item[0], item[1].id),
    )
  ]


def validate_extractive_grounding(samples: list[QuerySample]) -> list[str]:
  errors = []
  for sample in samples:
    if not sample.answerable:
      continue
    support = sample.validation.get("support_quotes")
    if not isinstance(support, list) or not support:
      errors.append(f"{sample.id}: missing support quotes")
      continue
    flattened = support
    if sample.type == QueryType.MULTI_SECTION:
      if not all(isinstance(group, list) for group in support):
        errors.append(f"{sample.id}: multi-section support quotes must be grouped")
        continue
      flattened = [quote for group in support for quote in group]
    if not all(isinstance(quote, str) and quote for quote in flattened):
      errors.append(f"{sample.id}: invalid support quote")
      continue
    evidence_text = "\n".join(evidence.text for evidence in sample.evidences)
    for quote in flattened:
      if quote not in evidence_text:
        errors.append(f"{sample.id}: support quote not found in evidence")
  return errors


def greedy_deduplicate_and_select(
  samples: list[QuerySample],
  embeddings: np.ndarray,
  threshold: float,
) -> list[QuerySample]:
  norms = embeddings / np.maximum(np.linalg.norm(embeddings, axis=1, keepdims=True), 1e-12)
  selected, selected_indices = [], []
  for query_type, target in FINAL_TYPE_COUNTS.items():
    buckets: dict[str, list[int]] = defaultdict(list)
    for index, sample in enumerate(samples):
      if sample.type == query_type:
        buckets[_selection_category(sample)].append(index)
    for category, indices in buckets.items():
      buckets[category] = _round_robin_evidence_clusters(samples, indices)
    category_keys = sorted(buckets)
    while sum(item.type == query_type for item in selected) < target:
      made_progress = False
      for category in category_keys:
        while buckets[category]:
          index = buckets[category].pop(0)
          if any(float(norms[index] @ norms[other]) > threshold for other in selected_indices):
            continue
          selected.append(samples[index])
          selected_indices.append(index)
          made_progress = True
          break
        if sum(item.type == query_type for item in selected) == target:
          break
      if not made_progress:
        break
    actual = sum(item.type == query_type for item in selected)
    if actual < target:
      raise ValueError(f"After dedup {query_type} has {actual}/{target} samples")
  return selected


def _selection_category(sample: QuerySample) -> str:
  if not sample.evidences:
    return "unanswerable"
  return "+".join(sorted({
    str(evidence.metadata.get("category", "unknown"))
    for evidence in sample.evidences
  }))


def _round_robin_evidence_clusters(
  samples: list[QuerySample],
  indices: list[int],
) -> list[int]:
  clusters: dict[tuple[tuple[object, ...], ...], list[int]] = defaultdict(list)
  for index in indices:
    sample = samples[index]
    key = tuple(sorted(
      (
        evidence.document_id,
        *evidence.heading_path,
      )
      for evidence in [*sample.evidences, *sample.negative_evidences]
    ))
    clusters[key].append(index)
  output = []
  cluster_keys = sorted(clusters, key=str)
  while True:
    made_progress = False
    for key in cluster_keys:
      if clusters[key]:
        output.append(clusters[key].pop(0))
        made_progress = True
    if not made_progress:
      return output


def exact_stratified_pending_split(
  samples: list[QuerySample],
  seed: int = 42,
) -> tuple[list[QuerySample], list[QuerySample]]:
  randomizer = random.Random(seed)
  query_types = list(FINAL_TYPE_COUNTS)
  test_targets = tuple(
    FINAL_TYPE_COUNTS[query_type] - DEV_TYPE_COUNTS[query_type]
    for query_type in query_types
  )
  components = _leakage_components(samples)
  randomizer.shuffle(components)
  feature_names = sorted({
    str(evidence.metadata.get("category"))
    for sample in samples
    for evidence in sample.evidences
  }) + ["repository:advanced-java"]
  feature_index = {name: index for index, name in enumerate(feature_names)}

  def feature_mask(component: list[int]) -> int:
    values = {
      str(evidence.metadata.get("category"))
      for index in component
      for evidence in samples[index].evidences
    }
    if any(
      evidence.metadata.get("repository") == "advanced-java"
      for index in component
      for evidence in samples[index].evidences
    ):
      values.add("repository:advanced-java")
    mask = 0
    for value in values:
      mask |= 1 << feature_index[value]
    return mask

  component_masks = [feature_mask(component) for component in components]
  feature_frequency = Counter(
    feature
    for mask in component_masks
    for feature in range(len(feature_names))
    if mask & (1 << feature)
  )
  ordered = sorted(
    zip(components, component_masks, strict=True),
    key=lambda item: (
      sum(feature_frequency[feature] for feature in range(len(feature_names))
          if item[1] & (1 << feature)),
      -item[1].bit_count(),
    ),
  )
  components = [component for component, _ in ordered]
  component_masks = [mask for _, mask in ordered]
  contributions = [
    tuple(
      sum(samples[index].type == query_type for index in component)
      for query_type in query_types
    )
    for component in components
  ]
  zero = tuple(0 for _ in query_types)
  full_mask = (1 << len(feature_names)) - 1
  dev_reserved: list[int] = []
  dev_reserved_counts = zero
  dev_covered_mask = 0
  feature_order = sorted(
    range(len(feature_names)),
    key=lambda feature: feature_frequency[feature],
  )
  for feature in feature_order:
    bit = 1 << feature
    if dev_covered_mask & bit:
      continue
    candidates = [
      index for index, mask in enumerate(component_masks)
      if mask & bit and index not in dev_reserved
      and all(
        dev_reserved_counts[type_index] + contributions[index][type_index]
        <= DEV_TYPE_COUNTS[query_types[type_index]]
        for type_index in range(len(query_types))
      )
      and all(
        any(
          other != index
          and other not in dev_reserved
          and component_masks[other] & (1 << required_feature)
          for other in range(len(components))
        )
        for required_feature in range(len(feature_names))
      )
    ]
    if not candidates:
      raise ValueError(
        f"Need independent Dev/Test evidence clusters for feature: {feature_names[feature]}"
      )
    chosen_index = min(
      candidates,
      key=lambda index: (
        sum(contributions[index]),
        -(component_masks[index] & ~dev_covered_mask).bit_count(),
        index,
      ),
    )
    dev_reserved.append(chosen_index)
    dev_reserved_counts = tuple(
      dev_reserved_counts[index] + contributions[chosen_index][index]
      for index in range(len(query_types))
    )
    dev_covered_mask |= component_masks[chosen_index]
  if dev_covered_mask != full_mask:
    raise ValueError("Reserved Dev components do not cover all category/source features")
  dev_reserved_set = set(dev_reserved)
  mandatory: list[int] = []
  mandatory_counts = zero
  covered_mask = 0
  for feature in feature_order:
    bit = 1 << feature
    if covered_mask & bit:
      continue
    candidates = [
      index for index, mask in enumerate(component_masks)
      if mask & bit and index not in mandatory and index not in dev_reserved_set
      and all(
        mandatory_counts[type_index] + contributions[index][type_index]
        <= test_targets[type_index]
        for type_index in range(len(query_types))
      )
    ]
    if not candidates:
      raise ValueError(f"Cannot place required test feature: {feature_names[feature]}")
    chosen_index = min(
      candidates,
      key=lambda index: (
        sum(contributions[index]),
        sum(
          contributions[index][type_index] / max(1, test_targets[type_index])
          for type_index in range(len(query_types))
        ),
        -(component_masks[index] & ~covered_mask).bit_count(),
        index,
      ),
    )
    mandatory.append(chosen_index)
    mandatory_counts = tuple(
      mandatory_counts[index] + contributions[chosen_index][index]
      for index in range(len(query_types))
    )
    covered_mask |= component_masks[chosen_index]
  if covered_mask != full_mask:
    raise ValueError("Mandatory test components do not cover all category/source features")
  states: dict[tuple[int, ...], tuple[int, ...]] = {
    mandatory_counts: tuple(mandatory),
  }
  mandatory_set = set(mandatory)
  for component_index, contribution in enumerate(contributions):
    if component_index in mandatory_set or component_index in dev_reserved_set:
      continue
    additions: dict[tuple[int, ...], tuple[int, ...]] = {}
    for state, chosen in list(states.items()):
      candidate = tuple(
        state[index] + contribution[index] for index in range(len(query_types))
      )
      if any(candidate[index] > test_targets[index] for index in range(len(query_types))):
        continue
      additions.setdefault(candidate, chosen + (component_index,))
    states.update(additions)
    if test_targets in states:
      break
  solution = states.get(test_targets)
  if solution is None:
    raise ValueError(
      "Cannot create an exact 80/40 split after reserving all category/source features"
    )
  test_component_indices = set(solution)
  test_sample_indices = {
    sample_index
    for component_index in test_component_indices
    for sample_index in components[component_index]
  }
  dev, test = [], []
  for index, sample in enumerate(samples):
    sample.review_status = "PENDING_HUMAN"
    if index in test_sample_indices:
      sample.split = "test"
      test.append(sample)
    else:
      sample.split = "dev"
      dev.append(sample)
  if len(dev) != 80 or len(test) != 40:
    raise AssertionError(f"Expected 80/40 split, got {len(dev)}/{len(test)}")
  return sorted(dev, key=lambda item: item.id), sorted(test, key=lambda item: item.id)


def _leakage_components(samples: list[QuerySample]) -> list[list[int]]:
  parents = list(range(len(samples)))

  def find(index: int) -> int:
    while parents[index] != index:
      parents[index] = parents[parents[index]]
      index = parents[index]
    return index

  def union(left: int, right: int) -> None:
    left_root, right_root = find(left), find(right)
    if left_root != right_root:
      parents[right_root] = left_root

  owners: dict[tuple[object, ...], int] = {}
  for index, sample in enumerate(samples):
    keys: list[tuple[object, ...]] = [
      ("evidence", evidence_id) for evidence_id in sample.negative_evidence_ids
    ]
    for evidence in sample.evidences:
      keys.extend((
        ("evidence", evidence.id),
        ("section", evidence.document_id, *evidence.heading_path),
      ))
    for check in sample.validation.get("negative_evidence_checks", []):
      if isinstance(check, dict):
        keys.append((
          "section",
          check.get("document_id"),
          *check.get("heading_path", []),
        ))
    for key in keys:
      if key in owners:
        union(index, owners[key])
      else:
        owners[key] = index
  groups: dict[int, list[int]] = defaultdict(list)
  for index in range(len(samples)):
    groups[find(index)].append(index)
  return list(groups.values())
