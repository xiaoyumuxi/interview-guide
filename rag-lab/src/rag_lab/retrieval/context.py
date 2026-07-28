from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from rag_lab.common.text import token_count, token_spans
from rag_lab.evaluation.spans import merge_intervals
from rag_lab.models import DocumentChunk
from rag_lab.retrieval.exact import SearchResult


@dataclass(frozen=True)
class ContextSpan:
  document_id: str
  start_offset: int
  end_offset: int
  text: str
  heading_path: tuple[str, ...]
  source_chunk_ids: tuple[str, ...] = ()


@dataclass
class AssembledContext:
  spans: list[ContextSpan] = field(default_factory=list)
  tokens: int = 0

  @property
  def text(self) -> str:
    return "\n\n".join(span.text for span in self.spans)


class ContextAssembler:
  def __init__(
    self,
    chunks: list[DocumentChunk],
    *,
    max_tokens: int = 3000,
    deduplicate: bool = True,
    neighbor_expansion: bool = True,
    parent_expansion: bool = True,
    max_chunks_per_section: int = 2,
  ) -> None:
    self.by_id = {chunk.id: chunk for chunk in chunks}
    self.by_section: dict[tuple[str, tuple[str, ...]], list[DocumentChunk]] = defaultdict(list)
    for chunk in chunks:
      self.by_section[(chunk.document_id, tuple(chunk.heading_path))].append(chunk)
    for section_chunks in self.by_section.values():
      section_chunks.sort(key=lambda chunk: (chunk.start_offset, chunk.end_offset))
    self.max_tokens = max_tokens
    self.deduplicate = deduplicate
    self.neighbor_expansion = neighbor_expansion
    self.parent_expansion = parent_expansion
    self.max_chunks_per_section = max_chunks_per_section

  def assemble(self, ranked: list[SearchResult]) -> AssembledContext:
    candidates: list[DocumentChunk] = [result.chunk for result in ranked]
    if self.neighbor_expansion:
      for result in ranked:
        for neighbor_id in (result.chunk.previous_id, result.chunk.next_id):
          if neighbor_id and neighbor_id in self.by_id:
            candidates.append(self.by_id[neighbor_id])
    if self.parent_expansion:
      for result in ranked:
        if result.chunk.parent_id and result.chunk.parent_id in self.by_id:
          candidates.append(self.by_id[result.chunk.parent_id])
        elif result.chunk.heading_path:
          candidates.extend(self.by_section[
            (result.chunk.document_id, tuple(result.chunk.heading_path))
          ])
    candidates = list({chunk.id: chunk for chunk in candidates}.values())

    assembled = AssembledContext()
    covered: dict[str, list[tuple[int, int]]] = defaultdict(list)
    section_counts: dict[tuple[str, tuple[str, ...]], int] = defaultdict(int)
    for chunk in candidates:
      if assembled.tokens >= self.max_tokens:
        break
      section = (chunk.document_id, tuple(chunk.heading_path))
      if section_counts[section] >= self.max_chunks_per_section:
        continue
      fragments = self._uncovered_fragments(chunk, covered[chunk.document_id])
      for start, end, text in fragments:
        remaining = self.max_tokens - assembled.tokens
        fragment_tokens = token_count(text)
        if fragment_tokens > remaining:
          token_windows = token_spans(text)[:remaining]
          if not token_windows:
            break
          truncated_end = token_windows[-1].end
          end = start + truncated_end
          text = text[:truncated_end]
          fragment_tokens = len(token_windows)
        assembled.spans.append(ContextSpan(
          document_id=chunk.document_id,
          start_offset=start,
          end_offset=end,
          text=text,
          heading_path=tuple(chunk.heading_path),
          source_chunk_ids=(chunk.id,),
        ))
        assembled.tokens += fragment_tokens
        covered[chunk.document_id] = merge_intervals(
          covered[chunk.document_id] + [(start, end)],
        )
        if assembled.tokens >= self.max_tokens:
          break
      if fragments:
        section_counts[section] += 1
    return assembled

  def _uncovered_fragments(
    self,
    chunk: DocumentChunk,
    covered: list[tuple[int, int]],
  ) -> list[tuple[int, int, str]]:
    start, end = chunk.start_offset, chunk.end_offset
    if not self.deduplicate:
      return [(start, end, chunk.source_text or chunk.text)]
    cursor = start
    intervals: list[tuple[int, int]] = []
    for covered_start, covered_end in merge_intervals(covered):
      if covered_end <= cursor or covered_start >= end:
        continue
      if covered_start > cursor:
        intervals.append((cursor, min(covered_start, end)))
      cursor = max(cursor, covered_end)
      if cursor >= end:
        break
    if cursor < end:
      intervals.append((cursor, end))
    source = chunk.source_text or chunk.text
    return [
      (fragment_start, fragment_end, source[fragment_start - start:fragment_end - start])
      for fragment_start, fragment_end in intervals
      if fragment_end > fragment_start
    ]
