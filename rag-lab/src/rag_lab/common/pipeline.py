from __future__ import annotations

import json
from pathlib import Path

from rag_lab.ingestion import MarkdownNormalizer, MarkItDownConverter
from rag_lab.models import StructuredDocument
from rag_lab.parsing import MarkdownStructureParser


def load_documents(
  raw_dir: Path,
  markdown_dir: Path | None = None,
) -> list[StructuredDocument]:
  converter = MarkItDownConverter()
  normalizer = MarkdownNormalizer()
  parser = MarkdownStructureParser()
  documents: list[StructuredDocument] = []
  paths = [
    path for path in sorted(raw_dir.rglob("*"))
    if path.is_file() and path.suffix.lower() in converter.SUPPORTED_SUFFIXES
  ]
  for path in paths:
    converted = converter.convert(path)
    converted.normalized_markdown = normalizer.normalize(converted.raw_markdown)
    if markdown_dir is not None:
      output_dir = markdown_dir / converted.document_id
      output_dir.mkdir(parents=True, exist_ok=True)
      (output_dir / "raw.md").write_text(converted.raw_markdown, encoding="utf-8")
      (output_dir / "normalized.md").write_text(converted.normalized_markdown, encoding="utf-8")
      (output_dir / "metadata.json").write_text(
        json.dumps(converted.metadata | {
          "document_id": converted.document_id,
          "source_path": str(converted.source_path),
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
      )
    documents.append(parser.parse(
      converted.document_id,
      converted.normalized_markdown,
      str(converted.source_path),
    ))
  return documents

