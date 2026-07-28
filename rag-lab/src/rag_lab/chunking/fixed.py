from __future__ import annotations

from rag_lab.chunking.base import add_links
from rag_lab.common.text import stable_id, token_spans
from rag_lab.models import DocumentChunk, StructuredDocument


class FixedChunker:
  name = "fixed"

  def __init__(self, chunk_size: int = 512, overlap: int = 64) -> None:
    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
      raise ValueError("Expected chunk_size > overlap >= 0")
    self.chunk_size = chunk_size
    self.overlap = overlap

  def chunk(self, document: StructuredDocument) -> list[DocumentChunk]:
    tokens = token_spans(document.markdown)
    if not tokens:
      return []
    chunks: list[DocumentChunk] = []
    step = self.chunk_size - self.overlap
    for token_start in range(0, len(tokens), step):
      window = tokens[token_start: token_start + self.chunk_size]
      if not window:
        break
      start, end = window[0].start, window[-1].end
      chunks.append(DocumentChunk(
        id=stable_id("chunk", self.name, document.document_id, start, end),
        document_id=document.document_id,
        text=document.markdown[start:end],
        start_offset=start,
        end_offset=end,
        heading_path=self._heading_path(document, start),
        metadata={"strategy": self.name, "indexable": True},
      ))
      if token_start + self.chunk_size >= len(tokens):
        break
    return add_links(chunks)

  @staticmethod
  def _heading_path(document: StructuredDocument, offset: int) -> list[str]:
    path: list[str] = []
    for block in document.blocks:
      if block.start_offset > offset:
        break
      if block.heading_level:
        path = block.heading_path
    return path.copy()

