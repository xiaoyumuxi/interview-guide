from __future__ import annotations

from rag_lab.chunking.base import add_links
from rag_lab.chunking.structure import StructureAwareChunker
from rag_lab.common.text import stable_id, token_count, token_spans
from rag_lab.models import DocumentChunk, StructuredDocument


class ParentChildChunker:
  name = "parent_child"

  def __init__(self, child_max_tokens: int = 256, heading_prefix: bool = True) -> None:
    self.child_max_tokens = child_max_tokens
    self.heading_prefix = heading_prefix

  def chunk(self, document: StructuredDocument) -> list[DocumentChunk]:
    parents: list[DocumentChunk] = []
    children: list[DocumentChunk] = []
    sections = StructureAwareChunker._sections(document)
    for section in sections:
      if not section.blocks:
        continue
      start, end = section.blocks[0].start_offset, section.blocks[-1].end_offset
      parent_id = stable_id("parent", document.document_id, start, end)
      parent = DocumentChunk(
        id=parent_id,
        document_id=document.document_id,
        text=document.markdown[start:end].strip(),
        start_offset=start,
        end_offset=end,
        heading_path=section.heading_path.copy(),
        metadata={"strategy": self.name, "role": "parent", "indexable": False},
        source_text=document.markdown[start:end],
        embedding_text=(
          f"{' > '.join(section.heading_path)}\n\n{document.markdown[start:end].strip()}"
          if self.heading_prefix and section.heading_path
          else document.markdown[start:end].strip()
        ),
      )
      parents.append(parent)
      for block in section.blocks:
        spans = token_spans(document.markdown[block.start_offset:block.end_offset])
        windows = [
          spans[index:index + self.child_max_tokens]
          for index in range(0, len(spans), self.child_max_tokens)
        ] or [[]]
        for window in windows:
          if not window:
            continue
          child_start = block.start_offset + window[0].start
          child_end = block.start_offset + window[-1].end
          child = DocumentChunk(
            id=stable_id("child", document.document_id, child_start, child_end),
            document_id=document.document_id,
            text=document.markdown[child_start:child_end],
            start_offset=child_start,
            end_offset=child_end,
            heading_path=section.heading_path.copy(),
            parent_id=parent_id,
            metadata={
              "strategy": self.name,
              "role": "child",
              "indexable": True,
              "heading_prefix": self.heading_prefix,
              "token_count": token_count(document.markdown[child_start:child_end]),
            },
            source_text=document.markdown[child_start:child_end],
            embedding_text=(
              f"{' > '.join(section.heading_path)}\n\n"
              f"{document.markdown[child_start:child_end]}"
              if self.heading_prefix and section.heading_path
              else document.markdown[child_start:child_end]
            ),
          )
          children.append(child)
    add_links(children)
    return parents + children
