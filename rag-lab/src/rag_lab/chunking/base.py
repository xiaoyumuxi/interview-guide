from __future__ import annotations

from typing import Protocol

from rag_lab.common.text import token_count
from rag_lab.models import DocumentChunk, StructuredDocument


class Chunker(Protocol):
  name: str

  def chunk(self, document: StructuredDocument) -> list[DocumentChunk]: ...


def add_links(chunks: list[DocumentChunk]) -> list[DocumentChunk]:
  for index, chunk in enumerate(chunks):
    chunk.previous_id = chunks[index - 1].id if index else None
    chunk.next_id = chunks[index + 1].id if index + 1 < len(chunks) else None
    chunk.metadata.setdefault("token_count", token_count(chunk.text))
  return chunks


def embedding_text(chunk: DocumentChunk, heading_prefix: bool) -> str:
  if chunk.embedding_text != chunk.text:
    return chunk.embedding_text or chunk.text
  if heading_prefix and chunk.heading_path:
    chunk.embedding_text = f"{' > '.join(chunk.heading_path)}\n\n{chunk.text}"
  else:
    chunk.embedding_text = chunk.text
  return chunk.embedding_text
