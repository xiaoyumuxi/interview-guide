from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any


class NodeType(StrEnum):
  DOCUMENT = "DOCUMENT"
  HEADING = "HEADING"
  PARAGRAPH = "PARAGRAPH"
  LIST = "LIST"
  LIST_ITEM = "LIST_ITEM"
  CODE_BLOCK = "CODE_BLOCK"
  TABLE = "TABLE"
  QUOTE = "QUOTE"


@dataclass
class ConvertedDocument:
  document_id: str
  source_path: Path
  raw_markdown: str
  normalized_markdown: str = ""
  metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentNode:
  id: str
  node_type: NodeType
  text: str
  heading_level: int | None
  heading_path: list[str]
  start_offset: int
  end_offset: int
  metadata: dict[str, Any] = field(default_factory=dict)
  children: list["DocumentNode"] = field(default_factory=list)


@dataclass
class StructuredDocument:
  document_id: str
  markdown: str
  root: DocumentNode
  source_path: str = ""

  @property
  def blocks(self) -> list[DocumentNode]:
    return self.root.children


@dataclass
class DocumentChunk:
  id: str
  document_id: str
  text: str
  start_offset: int
  end_offset: int
  heading_path: list[str]
  parent_id: str | None = None
  previous_id: str | None = None
  next_id: str | None = None
  metadata: dict[str, Any] = field(default_factory=dict)
  source_text: str | None = None
  embedding_text: str | None = None

  def __post_init__(self) -> None:
    # ``text`` remains the compatibility field used by the Phase 1 chunkers.
    # Metric V2 uses source offsets/source_text, while retrieval uses
    # embedding_text. Keeping these values explicit prevents injected headings
    # from leaking into source-span evaluation.
    if self.source_text is None:
      self.source_text = self.text
    if self.embedding_text is None:
      self.embedding_text = self.text

  def to_dict(self) -> dict[str, Any]:
    return asdict(self)
