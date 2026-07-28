from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Protocol

from rag_lab.models import DocumentChunk
from rag_lab.retrieval.exact import ExactDenseRetriever, SearchResult


class MultiSectionQueryDetector:
  _strong_signals = re.compile(r"区别|比较|相比|分别|各自|以及|同时|为什么.+而")
  _list_signal = re.compile(r"[^，。？?]+、[^，。？?]+(?:、|(?:和|与))[^，。？?]+")

  def detect(self, query: str) -> bool:
    normalized = query.strip()
    if self._strong_signals.search(normalized) or self._list_signal.search(normalized):
      return True
    # Weak binary conjunctions only identify a candidate. The decomposer still
    # refuses ambiguous single-concept wording.
    return bool(re.search(r"\S+(?:和|与)\S+", normalized))


class QueryDecomposer(Protocol):
  def decompose(self, query: str) -> list[str]: ...


class RuleBasedChineseQueryDecomposer:
  _why_but = re.compile(r"^为什么\s*(?P<left>.+?)，?而\s*(?P<right>.+?)[？?]?$")

  def __init__(self, max_subqueries: int = 4) -> None:
    self.max_subqueries = max_subqueries

  def decompose(self, query: str) -> list[str]:
    query = query.strip()
    if not query:
      return []
    why_match = self._why_but.match(query)
    if why_match:
      return self._limit([
        f"为什么{why_match.group('left').strip('，, ')}？",
        f"为什么{why_match.group('right').strip('，, ')}？",
      ])

    if "分别" in query or "各自" in query:
      marker = "分别" if "分别" in query else "各自"
      prefix, suffix = query.split(marker, 1)
      items = self._split_items(prefix)
      if len(items) >= 2:
        predicate = suffix.lstrip("，, ").rstrip("？?。")
        return self._limit([f"{item}{predicate}？" for item in items])

    comparison_body = re.sub(
      r"(?:有什么)?(?:区别|差异|异同)(?:是什么|有哪些)?[？?]?$", "", query,
    ).strip()
    conjunction = re.search(r"\s*(和|与|相比)\s*", comparison_body)
    if conjunction and comparison_body != query:
      left = comparison_body[:conjunction.start()].strip()
      remainder = comparison_body[conjunction.end():].strip()
      if " 的" in remainder:
        right, topic = remainder.split(" 的", 1)
      else:
        right, topic = remainder, ""
      right, topic = right.strip(), topic.strip()
      if topic:
        return self._limit([
          f"{left} 的{topic}是什么？",
          f"{right} 的{topic}是什么？",
        ])
      return self._limit([f"{left} 是什么？", f"{right} 是什么？"])

    # A three-item enumeration is reliable even without “分别”.
    body = query.rstrip("？?。")
    clause_match = re.match(r"^(?P<items>.+?(?:、.+?){1,}(?:和|与).+?)(?P<suffix>如何.+|为什么.+|各有什么.+)$", body)
    if clause_match:
      items = self._split_items(clause_match.group("items"))
      if len(items) >= 3:
        suffix = clause_match.group("suffix")
        return self._limit([f"{item}{suffix}？" for item in items])
    return []

  @staticmethod
  def _split_items(text: str) -> list[str]:
    cleaned = text.strip("，, ：:；;")
    return [
      item.strip("，, ")
      for item in re.split(r"\s*(?:、|以及|和|与)\s*", cleaned)
      if item.strip("，, ")
    ]

  def _limit(self, queries: list[str]) -> list[str]:
    deduplicated = list(dict.fromkeys(queries))
    return deduplicated[:self.max_subqueries]


def reciprocal_rank_fusion(
  result_lists: list[list[SearchResult]],
  *,
  rrf_k: int = 60,
) -> list[SearchResult]:
  scores: dict[str, float] = defaultdict(float)
  chunks: dict[str, DocumentChunk] = {}
  traces: dict[str, list[tuple[str, int, float]]] = defaultdict(list)
  for results in result_lists:
    for result in results:
      scores[result.chunk.id] += 1.0 / (rrf_k + result.rank)
      chunks[result.chunk.id] = result.chunk
      traces[result.chunk.id].append((
        result.source_query or "",
        result.source_rank or result.rank,
        result.dense_score if result.dense_score is not None else result.score,
      ))
  ordered_ids = sorted(
    scores,
    key=lambda chunk_id: (
      -scores[chunk_id],
      -max(trace[2] for trace in traces[chunk_id]),
      chunk_id,
    ),
  )
  fused = []
  for rank, chunk_id in enumerate(ordered_ids, start=1):
    source_query, source_rank, dense_score = max(
      traces[chunk_id], key=lambda trace: trace[2],
    )
    fused.append(SearchResult(
      chunk=chunks[chunk_id],
      score=scores[chunk_id],
      rank=rank,
      source_query=source_query,
      source_rank=source_rank,
      rrf_score=scores[chunk_id],
      dense_score=dense_score,
      sources=tuple(traces[chunk_id]),
    ))
  return fused


@dataclass
class SectionDiversityReranker:
  max_chunks_per_section_in_top_k: int = 2

  def rerank(self, results: list[SearchResult], top_k: int) -> list[SearchResult]:
    counts: dict[tuple[str, tuple[str, ...]], int] = defaultdict(int)
    selected: list[SearchResult] = []
    for result in results:
      key = (result.chunk.document_id, tuple(result.chunk.heading_path))
      if counts[key] >= self.max_chunks_per_section_in_top_k:
        continue
      counts[key] += 1
      selected.append(result)
      if len(selected) == top_k:
        break
    return [
      SearchResult(
        **{**result.__dict__, "rank": rank},
      )
      for rank, result in enumerate(selected, start=1)
    ]


class MultiQueryRetriever:
  def __init__(
    self,
    retriever: ExactDenseRetriever,
    *,
    detector: MultiSectionQueryDetector | None = None,
    decomposer: QueryDecomposer | None = None,
    candidate_top_n: int = 20,
    max_subqueries: int = 4,
    include_original_query: bool = True,
    rrf_k: int = 60,
    diversity_reranker: SectionDiversityReranker | None = None,
  ) -> None:
    self.retriever = retriever
    self.detector = detector or MultiSectionQueryDetector()
    self.decomposer = decomposer or RuleBasedChineseQueryDecomposer(max_subqueries)
    self.candidate_top_n = candidate_top_n
    self.max_subqueries = max_subqueries
    self.include_original_query = include_original_query
    self.rrf_k = rrf_k
    self.diversity_reranker = diversity_reranker
    self.generated_subqueries = 0
    self.query_embeddings = 0
    self.retrieval_calls = 0
    self.candidate_results = 0

  def search(self, query: str, top_k: int) -> list[SearchResult]:
    subqueries = (
      self.decomposer.decompose(query)[:self.max_subqueries]
      if self.detector.detect(query) else []
    )
    if not subqueries:
      self.query_embeddings += 1
      self.retrieval_calls += 1
      results = self.retriever.search(query, top_k)
      self.candidate_results += len(results)
      return results
    queries = ([query] if self.include_original_query else []) + subqueries
    self.generated_subqueries += len(subqueries)
    self.query_embeddings += len(queries)
    self.retrieval_calls += len(queries)
    lists = [self.retriever.search(item, self.candidate_top_n) for item in queries]
    self.candidate_results += sum(len(results) for results in lists)
    fused = reciprocal_rank_fusion(lists, rrf_k=self.rrf_k)
    if self.diversity_reranker:
      return self.diversity_reranker.rerank(fused, top_k)
    return [
      SearchResult(**{**result.__dict__, "rank": rank})
      for rank, result in enumerate(fused[:top_k], start=1)
    ]
