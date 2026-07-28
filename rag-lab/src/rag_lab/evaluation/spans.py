from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from typing import Protocol


class SourceSpan(Protocol):
  document_id: str
  start_offset: int
  end_offset: int


def merge_intervals(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
  """Merge overlapping or adjacent half-open intervals."""
  if not intervals:
    return []
  ordered = sorted(intervals)
  merged: list[tuple[int, int]] = []
  for start, end in ordered:
    if start < 0 or end < start:
      raise ValueError(f"Invalid half-open interval: ({start}, {end})")
    if start == end:
      continue
    if merged and start <= merged[-1][1]:
      merged[-1] = (merged[-1][0], max(merged[-1][1], end))
    else:
      merged.append((start, end))
  return merged


def spans_by_document(spans: Iterable[SourceSpan]) -> dict[str, list[tuple[int, int]]]:
  grouped: dict[str, list[tuple[int, int]]] = defaultdict(list)
  for span in spans:
    grouped[span.document_id].append((span.start_offset, span.end_offset))
  return {document_id: merge_intervals(intervals)
          for document_id, intervals in grouped.items()}


def intervals_length(intervals: Iterable[tuple[int, int]]) -> int:
  return sum(end - start for start, end in intervals)


def intersection_length(
  left: list[tuple[int, int]],
  right: list[tuple[int, int]],
) -> int:
  """Return intersection length of two already merged interval lists."""
  left = merge_intervals(left)
  right = merge_intervals(right)
  total = 0
  left_index = right_index = 0
  while left_index < len(left) and right_index < len(right):
    left_start, left_end = left[left_index]
    right_start, right_end = right[right_index]
    total += max(0, min(left_end, right_end) - max(left_start, right_start))
    if left_end <= right_end:
      left_index += 1
    else:
      right_index += 1
  return total


def span_coverage(span: SourceSpan, retrieved: dict[str, list[tuple[int, int]]]) -> float:
  length = max(1, span.end_offset - span.start_offset)
  covered = intersection_length(
    [(span.start_offset, span.end_offset)],
    retrieved.get(span.document_id, []),
  )
  return covered / length


def covered_span_characters(
  spans: Iterable[SourceSpan],
  retrieved: dict[str, list[tuple[int, int]]],
) -> tuple[int, int]:
  covered = total = 0
  for span in spans:
    span_length = max(0, span.end_offset - span.start_offset)
    total += span_length
    covered += intersection_length(
      [(span.start_offset, span.end_offset)],
      retrieved.get(span.document_id, []),
    )
  return covered, total


def context_precision(
  context_spans: Iterable[SourceSpan],
  gold_spans: Iterable[SourceSpan],
) -> float:
  context = spans_by_document(context_spans)
  gold = spans_by_document(gold_spans)
  denominator = sum(intervals_length(intervals) for intervals in context.values())
  if denominator == 0:
    return 0.0
  relevant = sum(
    intersection_length(intervals, gold.get(document_id, []))
    for document_id, intervals in context.items()
  )
  return relevant / denominator
