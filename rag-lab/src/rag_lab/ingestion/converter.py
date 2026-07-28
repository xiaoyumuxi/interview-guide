from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Protocol

from rag_lab.models import ConvertedDocument


class DocumentConverter(Protocol):
  def convert(self, path: Path) -> ConvertedDocument: ...


class MarkItDownConverter:
  """Adapter around MarkItDown; direct text formats avoid lossy round-trips."""

  TEXT_SUFFIXES = {".md", ".markdown", ".txt"}
  SUPPORTED_SUFFIXES = TEXT_SUFFIXES | {".pdf", ".docx", ".html", ".htm"}

  def convert(self, path: Path) -> ConvertedDocument:
    suffix = path.suffix.lower()
    if suffix not in self.SUPPORTED_SUFFIXES:
      raise ValueError(f"Unsupported document type: {suffix}")
    if suffix in self.TEXT_SUFFIXES:
      markdown = path.read_text(encoding="utf-8")
    else:
      try:
        from markitdown import MarkItDown
      except ImportError as exc:
        raise RuntimeError("Install project dependencies to convert binary documents") from exc
      result = MarkItDown().convert(str(path))
      markdown = result.text_content
    digest = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    return ConvertedDocument(
      document_id=f"{path.stem}-{digest}",
      source_path=path,
      raw_markdown=markdown,
      metadata={"source_suffix": suffix, "source_sha256": digest},
    )

