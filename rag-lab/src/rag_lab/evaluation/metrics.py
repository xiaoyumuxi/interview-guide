from __future__ import annotations

import math
import statistics
from collections import defaultdict
from typing import Any

from rag_lab.dataset.models import Evidence, QuerySample
from rag_lab.evaluation.spans import (
  context_precision,
  covered_span_characters,
  span_coverage,
  spans_by_document,
)
from rag_lab.models import DocumentChunk
from rag_lab.retrieval.exact import SearchResult


def evidence_coverage(result: SearchResult, evidence: Evidence) -> float:
  """Compatibility helper for coverage by one chunk."""
  return span_coverage(evidence, spans_by_document([result.chunk]))


def evidence_coverages(
  chunks: list[DocumentChunk],
  evidences: list[Evidence],
) -> list[float]:
  retrieved = spans_by_document(chunks)
  return [span_coverage(evidence, retrieved) for evidence in evidences]


def evaluate_results(
  samples: list[QuerySample],
  results: dict[str, list[SearchResult]],
  top_ks: list[int],
  coverage_threshold: float | None = None,
  parents: dict[str, Any] | None = None,
  *,
  coverage_thresholds: list[float] | None = None,
  primary_threshold: float | None = None,
  any_overlap_threshold: float = 0.01,
) -> dict[str, Any]:
  """Evaluate ranked retrieval results with source-span Metric V2.

  ``coverage_threshold`` remains accepted for Phase 1 callers. If supplied by
  itself it becomes the primary threshold, while the V2 threshold family still
  defaults to 25/50/75 percent.
  """
  thresholds = coverage_thresholds or [0.25, 0.50, 0.75]
  primary = primary_threshold if primary_threshold is not None else (
    coverage_threshold if coverage_threshold is not None else 0.50
  )
  answerable = [sample for sample in samples if sample.answerable]
  groups: dict[str, list[QuerySample]] = defaultdict(list)
  groups["Overall"] = answerable
  for sample in answerable:
    groups[sample.type.value].append(sample)
    if sample.negative_evidences:
      groups["NEGATIVE_BEARING"].append(sample)
    hard_type = sample.validation.get("hard_dev_type")
    if hard_type:
      groups[str(hard_type)].append(sample)

  output: dict[str, Any] = {}
  for group_name, group_samples in groups.items():
    rows = [
      _sample_metrics(
        sample,
        results[sample.id],
        top_ks,
        thresholds,
        primary,
        any_overlap_threshold,
        parents,
      )
      for sample in group_samples
    ]
    output[group_name] = _aggregate_rows(rows, top_ks)
  return output


def evaluate_assembled_contexts(
  samples: list[QuerySample],
  contexts: dict[str, dict[int, Any]],
  top_ks: list[int],
) -> dict[str, Any]:
  """Evaluate assembled contexts separately from retrieval rankings."""
  answerable = [sample for sample in samples if sample.answerable]
  groups: dict[str, list[QuerySample]] = defaultdict(list)
  groups["Overall"] = answerable
  for sample in answerable:
    groups[sample.type.value].append(sample)
    hard_type = sample.validation.get("hard_dev_type")
    if hard_type:
      groups[str(hard_type)].append(sample)
  output: dict[str, Any] = {}
  for group_name, group_samples in groups.items():
    rows: list[dict[str, float]] = []
    for sample in group_samples:
      row: dict[str, float] = {}
      for k in top_ks:
        context = contexts[sample.id][k]
        coverages = evidence_coverages(context.spans, sample.evidences)
        covered, total = covered_span_characters(
          sample.evidences, spans_by_document(context.spans),
        )
        row[f"ContextEvidenceCoverage@{k}"] = (
          statistics.fmean(coverages) if coverages else 0.0
        )
        row[f"ContextPrecision@{k}"] = context_precision(context.spans, sample.evidences)
        row[f"ContextWaste@{k}"] = 1.0 - row[f"ContextPrecision@{k}"]
        row[f"ApproxContextTokens@{k}"] = float(context.tokens)
        row[f"_ContextCovered@{k}"] = float(covered)
        row[f"_ContextTotal@{k}"] = float(total)
      rows.append(row)
    aggregated = {
      key: statistics.fmean(float(row[key]) for row in rows)
      for key in rows[0] if not key.startswith("_")
    } if rows else {}
    for k in top_ks:
      covered = sum(row[f"_ContextCovered@{k}"] for row in rows)
      total = sum(row[f"_ContextTotal@{k}"] for row in rows)
      aggregated[f"MicroContextEvidenceCoverage@{k}"] = covered / total if total else 0.0
    output[group_name] = aggregated
  return output


def _sample_metrics(
  sample: QuerySample,
  ranked: list[SearchResult],
  top_ks: list[int],
  thresholds: list[float],
  primary: float,
  any_overlap_threshold: float,
  parents: dict[str, Any] | None,
) -> dict[str, float | None]:
  metrics: dict[str, float | None] = {}
  metrics["_HardNegativeQuery"] = float(sample.type.value == "HARD_NEGATIVE")
  metrics["_NegativeBearingQuery"] = float(bool(sample.negative_evidences))
  first_rank = next(
    (
      result.rank for result in ranked
      if any(evidence_coverage(result, evidence) >= primary for evidence in sample.evidences)
    ),
    None,
  )
  metrics["MRR"] = 1.0 / first_rank if first_rank else 0.0
  metrics["_GoldCharacters"] = float(sum(
    evidence.end_offset - evidence.start_offset for evidence in sample.evidences
  ))

  for k in top_ks:
    chunks = [result.chunk for result in ranked[:k]]
    coverages = evidence_coverages(chunks, sample.evidences)
    covered_chars, total_chars = covered_span_characters(
      sample.evidences, spans_by_document(chunks),
    )
    macro = statistics.fmean(coverages) if coverages else 0.0
    metrics[f"EvidenceCoverage@{k}"] = macro
    metrics[f"MacroEvidenceCoverage@{k}"] = macro
    metrics[f"_CoveredGoldCharacters@{k}"] = float(covered_chars)
    metrics[f"_TotalGoldCharacters@{k}"] = float(total_chars)
    metrics[f"ContextPrecision@{k}"] = context_precision(chunks, sample.evidences)
    metrics[f"ContextWaste@{k}"] = 1.0 - float(metrics[f"ContextPrecision@{k}"])

    any_overlap_hits = [coverage >= any_overlap_threshold for coverage in coverages]
    metrics[f"AnyOverlapHitRate@{k}"] = float(any(any_overlap_hits))
    metrics[f"AnyOverlapRecall@{k}"] = (
      sum(any_overlap_hits) / len(any_overlap_hits) if any_overlap_hits else 0.0
    )
    for threshold in thresholds:
      label = _threshold_label(threshold)
      hits = [coverage >= threshold for coverage in coverages]
      metrics[f"EvidenceRecall@{k}/{label}"] = sum(hits) / len(hits) if hits else 0.0
      metrics[f"AllEvidenceHit@{k}/{label}"] = float(bool(hits) and all(hits))
      if math.isclose(threshold, primary):
        metrics[f"AllEvidenceHit@{k}"] = metrics[f"AllEvidenceHit@{k}/{label}"]

    if parents is not None:
      parent_chunks = [
        parents[result.chunk.parent_id]
        for result in ranked[:k]
        if result.chunk.parent_id and result.chunk.parent_id in parents
      ]
      parent_coverages = evidence_coverages(parent_chunks, sample.evidences)
      metrics[f"ParentCoverage@{k}"] = (
        sum(coverage >= primary for coverage in parent_coverages) / len(parent_coverages)
        if parent_coverages else 0.0
      )

  _add_negative_metrics(metrics, sample, ranked, top_ks, primary)
  return metrics


def _add_negative_metrics(
  metrics: dict[str, float | None],
  sample: QuerySample,
  ranked: list[SearchResult],
  top_ks: list[int],
  threshold: float,
) -> None:
  negatives = sample.negative_evidences
  if not negatives:
    return
  metrics["_GoldMappedQuery"] = 0.0
  metrics["_NegativeMappedQuery"] = 0.0
  metrics["_MarginEligibleQuery"] = 0.0
  metrics["PairwiseGoldWins"] = 0.0
  metrics["PairwiseGoldPairs"] = 0.0
  for k in top_ks:
    chunks = [result.chunk for result in ranked[:k]]
    negative_hits = [
      coverage >= threshold for coverage in evidence_coverages(chunks, negatives)
    ]
    metrics[f"NegativeExposure@{k}Query"] = float(any(negative_hits))
    metrics[f"NegativeExposure@{k}Evidence"] = sum(negative_hits) / len(negative_hits)
    gold_rank = _first_evidence_rank(ranked[:k], sample.evidences, threshold)
    negative_rank = _first_evidence_rank(ranked[:k], negatives, threshold)
    metrics[f"GoldBeforeNegative@{k}"] = float(
      gold_rank is not None and (negative_rank is None or gold_rank < negative_rank)
    )
    metrics[f"_GoldBeforeNegativeSuccess@{k}"] = metrics[f"GoldBeforeNegative@{k}"]
    metrics[f"_GoldBeforeNegativeQuery@{k}"] = 1.0

  gold_scores = [_best_evidence_score(ranked, evidence, threshold)
                 for evidence in sample.evidences]
  negative_scores = [_best_evidence_score(ranked, evidence, threshold)
                     for evidence in negatives]
  finite_gold = [score for score in gold_scores if score is not None]
  finite_negative = [score for score in negative_scores if score is not None]
  metrics["_GoldMappedQuery"] = float(bool(finite_gold))
  metrics["_NegativeMappedQuery"] = float(bool(finite_negative))
  if finite_gold and finite_negative:
    metrics["_MarginEligibleQuery"] = 1.0
    margin = max(finite_gold) - max(finite_negative)
    metrics["GoldNegativeScoreMargin"] = margin
    pairs = [(gold, negative) for gold in finite_gold for negative in finite_negative]
    metrics["PairwiseGoldWins"] = float(sum(gold > negative for gold, negative in pairs))
    metrics["PairwiseGoldPairs"] = float(len(pairs))


def _best_evidence_score(
  ranked: list[SearchResult],
  evidence: Evidence,
  threshold: float,
) -> float | None:
  scores = [
    result.score for result in ranked
    if evidence_coverage(result, evidence) >= threshold
  ]
  return max(scores) if scores else None


def _first_evidence_rank(
  ranked: list[SearchResult],
  evidences: list[Evidence],
  threshold: float,
) -> int | None:
  return next(
    (
      result.rank for result in ranked
      if any(evidence_coverage(result, evidence) >= threshold for evidence in evidences)
    ),
    None,
  )


def _aggregate_rows(
  rows: list[dict[str, float | None]],
  top_ks: list[int],
) -> dict[str, float]:
  if not rows:
    return {}
  output: dict[str, float] = {}
  output["QueryCount"] = float(len(rows))
  output["HardNegativeQueryCount"] = sum(
    float(row.get("_HardNegativeQuery", 0.0) or 0.0) for row in rows
  )
  output["NegativeBearingQueryCount"] = sum(
    float(row.get("_NegativeBearingQuery", 0.0) or 0.0) for row in rows
  )
  output["GoldMappedQueryCount"] = sum(
    float(row.get("_GoldMappedQuery", 0.0) or 0.0) for row in rows
  )
  output["NegativeMappedQueryCount"] = sum(
    float(row.get("_NegativeMappedQuery", 0.0) or 0.0) for row in rows
  )
  output["MarginEligibleQueryCount"] = sum(
    float(row.get("_MarginEligibleQuery", 0.0) or 0.0) for row in rows
  )
  public_keys = sorted({
    key for row in rows for key, value in row.items()
    if not key.startswith("_") and value is not None
    and key not in {"PairwiseGoldWins", "PairwiseGoldPairs", "GoldNegativeScoreMargin"}
  })
  for key in public_keys:
    values = [float(row[key]) for row in rows if row.get(key) is not None]
    if values:
      output[key] = statistics.fmean(values)
  for k in top_ks:
    covered = sum(float(row.get(f"_CoveredGoldCharacters@{k}", 0.0) or 0.0) for row in rows)
    total = sum(float(row.get(f"_TotalGoldCharacters@{k}", 0.0) or 0.0) for row in rows)
    output[f"MicroEvidenceCoverage@{k}"] = covered / total if total else 0.0

  margins = [
    float(row["GoldNegativeScoreMargin"])
    for row in rows if row.get("GoldNegativeScoreMargin") is not None
  ]
  if margins:
    output["AverageGoldNegativeScoreMargin"] = statistics.fmean(margins)
    output["P50GoldNegativeScoreMargin"] = statistics.median(margins)
    output["MinimumGoldNegativeScoreMargin"] = min(margins)
  wins = sum(float(row.get("PairwiseGoldWins", 0.0) or 0.0) for row in rows)
  pairs = sum(float(row.get("PairwiseGoldPairs", 0.0) or 0.0) for row in rows)
  output["PairwiseGoldWinCount"] = wins
  output["PairwiseComparisonCount"] = pairs
  if pairs:
    output["PairwiseGoldWinRate"] = wins / pairs
  for k in top_ks:
    successes = sum(
      float(row.get(f"_GoldBeforeNegativeSuccess@{k}", 0.0) or 0.0)
      for row in rows
    )
    eligible = sum(
      float(row.get(f"_GoldBeforeNegativeQuery@{k}", 0.0) or 0.0)
      for row in rows
    )
    output[f"GoldBeforeNegativeSuccessCount@{k}"] = successes
    output[f"GoldBeforeNegativeQueryCount@{k}"] = eligible
    if eligible:
      output[f"GoldBeforeNegativeRate@{k}"] = successes / eligible
  return output


def _threshold_label(threshold: float) -> str:
  return str(round(threshold * 100))
