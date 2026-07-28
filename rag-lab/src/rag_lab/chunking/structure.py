from __future__ import annotations

from dataclasses import dataclass

from rag_lab.chunking.base import add_links
from rag_lab.common.text import stable_id, token_count, token_spans
from rag_lab.models import DocumentChunk, DocumentNode, NodeType, StructuredDocument


@dataclass
class _Group:
  heading_path: list[str]
  blocks: list[DocumentNode]


class StructureAwareChunker:
  name = "structure"

  def __init__(self, max_tokens: int = 512, heading_prefix: bool = True) -> None:
    self.max_tokens = max_tokens
    self.heading_prefix = heading_prefix

  def chunk(self, document: StructuredDocument) -> list[DocumentChunk]:
    chunks: list[DocumentChunk] = []
    for group in self._sections(document):
      if not group.blocks:
        continue
      pending: list[DocumentNode] = []
      pending_tokens = 0
      for block in group.blocks:
        count = token_count(block.text)
        if count > self.max_tokens:
          if pending:
            chunks.append(self._from_blocks(document, group.heading_path, pending))
            pending, pending_tokens = [], 0
          chunks.extend(self._split_large_block(document, group.heading_path, block))
        elif pending and pending_tokens + count > self.max_tokens:
          chunks.append(self._from_blocks(document, group.heading_path, pending))
          pending, pending_tokens = [block], count
        else:
          pending.append(block)
          pending_tokens += count
      if pending:
        chunks.append(self._from_blocks(document, group.heading_path, pending))
    return add_links(chunks)

  @staticmethod
  def _sections(document: StructuredDocument) -> list[_Group]:
    groups: list[_Group] = []
    current = _Group([], [])
    for block in document.blocks:
      if block.node_type == NodeType.HEADING:
        if current.blocks:
          groups.append(current)
        current = _Group(block.heading_path, [])
      else:
        current.blocks.append(block)
    if current.blocks:
      groups.append(current)
    return groups

  def _from_blocks(
    self,
    document: StructuredDocument,
    heading_path: list[str],
    blocks: list[DocumentNode],
  ) -> DocumentChunk:
    start, end = blocks[0].start_offset, blocks[-1].end_offset
    source_text = document.markdown[start:end]
    body = source_text.strip()
    embedding = (
      f"{' > '.join(heading_path)}\n\n{body}"
      if self.heading_prefix and heading_path else body
    )
    return DocumentChunk(
      id=stable_id("chunk", self.name, document.document_id, start, end),
      document_id=document.document_id,
      text=body,
      start_offset=start,
      end_offset=end,
      heading_path=heading_path.copy(),
      metadata={
        "strategy": self.name,
        "indexable": True,
        "heading_prefix": self.heading_prefix,
        "block_types": [block.node_type for block in blocks],
      },
      source_text=source_text,
      embedding_text=embedding,
    )

  def _split_large_block(
    self,
    document: StructuredDocument,
    heading_path: list[str],
    block: DocumentNode,
  ) -> list[DocumentChunk]:
    if block.node_type == NodeType.TABLE and "|" in block.text:
      table_chunks = self._split_table(document, heading_path, block)
      if table_chunks:
        return table_chunks
    tokens = token_spans(document.markdown[block.start_offset:block.end_offset])
    chunks: list[DocumentChunk] = []
    for index in range(0, len(tokens), self.max_tokens):
      window = tokens[index:index + self.max_tokens]
      start = block.start_offset + window[0].start
      end = block.start_offset + window[-1].end
      chunks.append(DocumentChunk(
        id=stable_id("chunk", self.name, document.document_id, start, end),
        document_id=document.document_id,
        text=document.markdown[start:end],
        start_offset=start,
        end_offset=end,
        heading_path=heading_path.copy(),
        metadata={
          "strategy": self.name,
          "indexable": True,
          "heading_prefix": self.heading_prefix,
          "hard_split": True,
          "block_type": block.node_type,
        },
        source_text=document.markdown[start:end],
        embedding_text=(
          f"{' > '.join(heading_path)}\n\n{document.markdown[start:end]}"
          if self.heading_prefix and heading_path else document.markdown[start:end]
        ),
      ))
    return chunks

  def _split_table(
    self,
    document: StructuredDocument,
    heading_path: list[str],
    block: DocumentNode,
  ) -> list[DocumentChunk]:
    source = document.markdown[block.start_offset:block.end_offset]
    lines = source.splitlines(keepends=True)
    if len(lines) < 3:
      return []
    header = "".join(lines[:2]).strip()
    chunks: list[DocumentChunk] = []
    cursor = sum(len(line) for line in lines[:2])
    pending: list[tuple[int, str]] = []
    pending_tokens = token_count(header)
    for line in lines[2:]:
      line_tokens = token_count(line)
      if pending and pending_tokens + line_tokens > self.max_tokens:
        chunks.append(self._table_chunk(
          document, heading_path, block.start_offset, header, pending,
        ))
        pending, pending_tokens = [], token_count(header)
      pending.append((cursor, line))
      pending_tokens += line_tokens
      cursor += len(line)
    if pending:
      chunks.append(self._table_chunk(
        document, heading_path, block.start_offset, header, pending,
      ))
    return chunks

  def _table_chunk(
    self,
    document: StructuredDocument,
    heading_path: list[str],
    block_start: int,
    header: str,
    rows: list[tuple[int, str]],
  ) -> DocumentChunk:
    start = block_start + rows[0][0]
    end = block_start + rows[-1][0] + len(rows[-1][1])
    text = f"{header}\n{''.join(row for _, row in rows).strip()}"
    source_text = document.markdown[start:end]
    embedding = (
      f"{' > '.join(heading_path)}\n\n{text}"
      if self.heading_prefix and heading_path else text
    )
    return DocumentChunk(
      id=stable_id("chunk", self.name, document.document_id, start, end, "table"),
      document_id=document.document_id,
      text=text,
      start_offset=start,
      end_offset=end,
      heading_path=heading_path.copy(),
      metadata={
        "strategy": self.name,
        "indexable": True,
        "heading_prefix": self.heading_prefix,
        "hard_split": True,
        "block_type": NodeType.TABLE,
        "synthetic_table_header": header,
      },
      source_text=source_text,
      embedding_text=embedding,
    )
