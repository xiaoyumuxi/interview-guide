import json
from pathlib import Path

from rag_lab.models import DocumentChunk
from rag_lab.retrieval import (
  ContextAssembler,
  MultiQueryRetriever,
  MultiSectionQueryDetector,
  RuleBasedChineseQueryDecomposer,
  SearchResult,
  SectionDiversityReranker,
  reciprocal_rank_fusion,
)


def _chunk(
  chunk_id: str,
  start: int,
  end: int,
  heading: str = "H",
  *,
  parent_id: str | None = None,
) -> DocumentChunk:
  return DocumentChunk(
    chunk_id,
    "doc",
    "字" * (end - start),
    start,
    end,
    [heading],
    parent_id=parent_id,
    source_text="字" * (end - start),
  )


def test_query_detector_and_decomposer_golden() -> None:
  fixtures = json.loads(
    (Path(__file__).parent / "fixtures/multi_query_golden.json").read_text(),
  )
  detector = MultiSectionQueryDetector()
  decomposer = RuleBasedChineseQueryDecomposer()
  for fixture in fixtures:
    assert detector.detect(fixture["query"]) is fixture["should_detect"], fixture["name"]
    assert decomposer.decompose(fixture["query"]) == fixture["subqueries"], fixture["name"]


def test_rrf_uses_ranks_and_keeps_trace() -> None:
  first, second = _chunk("a", 0, 5), _chunk("b", 5, 10)
  fused = reciprocal_rank_fusion([
    [
      SearchResult(first, 0.9, 1, source_query="q", source_rank=1, dense_score=0.9),
      SearchResult(second, 0.8, 2, source_query="q", source_rank=2, dense_score=0.8),
    ],
    [
      SearchResult(second, 0.7, 1, source_query="sub", source_rank=1, dense_score=0.7),
    ],
  ])
  assert fused[0].chunk.id == "b"
  assert fused[0].rrf_score == 1 / 62 + 1 / 61
  assert len(fused[0].sources) == 2


def test_section_diversity_caps_each_section() -> None:
  results = [
    SearchResult(_chunk("a", 0, 2, "same"), 0.9, 1),
    SearchResult(_chunk("b", 2, 4, "same"), 0.8, 2),
    SearchResult(_chunk("c", 4, 6, "same"), 0.7, 3),
    SearchResult(_chunk("d", 6, 8, "other"), 0.6, 4),
  ]
  reranked = SectionDiversityReranker(2).rerank(results, 3)
  assert [result.chunk.id for result in reranked] == ["a", "b", "d"]
  assert [result.rank for result in reranked] == [1, 2, 3]


def test_context_deduplication() -> None:
  first = _chunk("a", 0, 6)
  second = _chunk("b", 3, 10, "H2")
  context = ContextAssembler(
    [first, second],
    max_tokens=20,
    neighbor_expansion=False,
    parent_expansion=False,
  ).assemble([SearchResult(first, 1, 1), SearchResult(second, 0.9, 2)])
  assert sum(span.end_offset - span.start_offset for span in context.spans) == 10
  assert [(span.start_offset, span.end_offset) for span in context.spans] == [(0, 6), (6, 10)]


def test_context_token_budget_and_parent_expansion() -> None:
  parent = _chunk("parent", 0, 20, "H")
  parent.metadata["indexable"] = False
  child = _chunk("child", 0, 5, "H", parent_id="parent")
  context = ContextAssembler(
    [parent, child],
    max_tokens=8,
    neighbor_expansion=False,
    parent_expansion=True,
    max_chunks_per_section=2,
  ).assemble([SearchResult(child, 1, 1)])
  assert context.tokens <= 8
  assert sum(span.end_offset - span.start_offset for span in context.spans) == 8


class _RecordingRetriever:
  def __init__(self) -> None:
    self.queries: list[str] = []

  def search(self, query: str, top_k: int) -> list[SearchResult]:
    self.queries.append(query)
    return [SearchResult(_chunk(f"c{len(self.queries)}", 0, 2), 1.0, 1)]


def test_no_gold_leakage_multi_query_api_only_uses_question() -> None:
  base = _RecordingRetriever()
  retriever = MultiQueryRetriever(base)  # type: ignore[arg-type]
  retriever.search("CMS 和 G1 有什么区别？", 5)
  assert base.queries
  assert all(isinstance(query, str) for query in base.queries)
