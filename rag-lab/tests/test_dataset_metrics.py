import numpy as np
import pytest

from rag_lab.dataset.models import Evidence, QuerySample, QueryType
from rag_lab.dataset.validator import DatasetValidator
from rag_lab.evaluation.metrics import evaluate_results, evidence_coverages
from rag_lab.evaluation.spans import context_precision, merge_intervals
from rag_lab.models import DocumentChunk, DocumentNode, NodeType, StructuredDocument
from rag_lab.retrieval import SearchResult


def _evidence(evidence_id: str, start: int, end: int) -> Evidence:
  text = "abcdefghij"[start:end]
  return Evidence(
    id=evidence_id,
    document_id="doc",
    heading_path=["H"],
    start_offset=start,
    end_offset=end,
    text=text,
  )


def test_validator_detects_offset_mismatch() -> None:
  document = StructuredDocument(
    "doc",
    "abcdefghij",
    DocumentNode("root", NodeType.DOCUMENT, "abcdefghij", None, [], 0, 10),
  )
  sample = QuerySample(
    id="q1",
    question="这个事实是什么？",
    reference_answer="wrong",
    evidences=[_evidence("e1", 0, 5).model_copy(update={"text": "WRONG"})],
    type=QueryType.DIRECT_FACT,
  )
  errors = DatasetValidator().validate([sample], {"doc": document})
  assert any("does not match offset" in error for error in errors)


def test_semantic_duplicate_threshold() -> None:
  samples = [
    QuerySample(id="q1", question="问题一是什么", reference_answer="a",
                evidences=[_evidence("e1", 0, 5)], type=QueryType.DIRECT_FACT),
    QuerySample(id="q2", question="问题二是什么", reference_answer="b",
                evidences=[_evidence("e2", 5, 10)], type=QueryType.DIRECT_FACT),
  ]
  duplicates = DatasetValidator.semantic_duplicates(
    samples, np.array([[1.0, 0.0], [0.95, 0.05]], dtype=np.float32), 0.9,
  )
  assert duplicates[0][:2] == ("q1", "q2")


def test_multi_evidence_recall_hitrate_and_mrr() -> None:
  sample = QuerySample(
    id="q1",
    question="比较两项机制",
    reference_answer="answer",
    evidences=[_evidence("e1", 0, 3), _evidence("e2", 7, 10)],
    type=QueryType.MULTI_SECTION,
  )
  wrong = DocumentChunk("c0", "other", "x", 0, 1, [])
  first = DocumentChunk("c1", "doc", "abc", 0, 3, ["H"])
  second = DocumentChunk("c2", "doc", "hij", 7, 10, ["H"])
  results = {
    "q1": [
      SearchResult(wrong, 0.9, 1),
      SearchResult(first, 0.8, 2),
      SearchResult(second, 0.7, 3),
    ],
  }
  metrics = evaluate_results([sample], results, [1, 2, 3])["Overall"]
  assert metrics["AllEvidenceHit@1"] == 0
  assert metrics["AnyOverlapHitRate@2"] == 1
  assert metrics["EvidenceRecall@2/50"] == 0.5
  assert metrics["EvidenceRecall@3/50"] == 1
  assert metrics["AllEvidenceHit@3/50"] == 1
  assert metrics["MRR"] == 0.5


def test_merge_intervals_merges_overlap_and_adjacency() -> None:
  assert merge_intervals([(8, 10), (0, 3), (2, 5), (5, 7)]) == [(0, 7), (8, 10)]


def test_evidence_coverage_single_span() -> None:
  evidence = _evidence("e1", 2, 8)
  chunk = DocumentChunk("c1", "doc", "cdef", 2, 6, ["H"])
  assert evidence_coverages([chunk], [evidence]) == [4 / 6]


def test_evidence_coverage_multiple_chunks_and_overlap_deduplication() -> None:
  evidence = _evidence("e1", 0, 10)
  chunks = [
    DocumentChunk("c1", "doc", "abcdef", 0, 6, ["H"]),
    DocumentChunk("c2", "doc", "defgh", 3, 8, ["H"]),
  ]
  assert evidence_coverages(chunks, [evidence]) == [0.8]


def test_context_precision_uses_merged_source_spans() -> None:
  chunks = [
    DocumentChunk("c1", "doc", "abcdef", 0, 6, ["H"]),
    DocumentChunk("c2", "doc", "defghij", 3, 10, ["H"]),
  ]
  evidence = [_evidence("e1", 2, 5)]
  assert context_precision(chunks, evidence) == 0.3


def test_heading_prefix_is_not_counted_in_context_denominator() -> None:
  chunk = DocumentChunk(
    "c1", "doc", "abcde", 0, 5, ["Long heading"],
    source_text="abcde",
    embedding_text="Long heading\n\nabcde",
  )
  assert context_precision([chunk], [_evidence("e1", 0, 5)]) == 1.0


def test_negative_exposure_margin_and_gold_before_negative() -> None:
  sample = QuerySample(
    id="q1",
    question="相近概念如何区分？",
    reference_answer="answer",
    evidences=[_evidence("gold", 0, 3)],
    negative_evidences=[_evidence("negative", 7, 10)],
    negative_evidence_ids=["negative"],
    type=QueryType.HARD_NEGATIVE,
  )
  gold = DocumentChunk("gold-chunk", "doc", "abc", 0, 3, ["H"])
  negative = DocumentChunk("negative-chunk", "doc", "hij", 7, 10, ["H"])
  metrics = evaluate_results(
    [sample],
    {"q1": [SearchResult(gold, 0.8, 1), SearchResult(negative, 0.6, 2)]},
    [1, 2],
  )["Overall"]
  assert metrics["NegativeExposure@1Query"] == 0
  assert metrics["NegativeExposure@2Evidence"] == 1
  assert metrics["AverageGoldNegativeScoreMargin"] == pytest.approx(0.2)
  assert metrics["PairwiseGoldWinRate"] == 1
  assert metrics["GoldBeforeNegative@2"] == 1
