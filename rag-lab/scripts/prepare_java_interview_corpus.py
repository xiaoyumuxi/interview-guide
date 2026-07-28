#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag_lab.corpus import REPOSITORIES, SELECTED_DOCUMENTS  # noqa: E402


def sha256(path: Path) -> str:
  return hashlib.sha256(path.read_bytes()).hexdigest()


def git_head(path: Path) -> str:
  return subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()


def main() -> None:
  sources_root = ROOT / "data/sources"
  corpus_root = ROOT / "data/corpus/java-interview-real-v1"
  corpus_root.mkdir(parents=True, exist_ok=True)
  selected_targets = {
    Path(selected.repository) / selected.path for selected in SELECTED_DOCUMENTS
  }
  for existing in corpus_root.rglob("*.md"):
    if existing.relative_to(corpus_root) not in selected_targets:
      existing.unlink()
  records = []
  for selected in SELECTED_DOCUMENTS:
    repository = REPOSITORIES[selected.repository]
    checkout = sources_root / repository.key
    if not checkout.is_dir():
      raise SystemExit(f"Missing checkout: {checkout}")
    actual_commit = git_head(checkout)
    if actual_commit != repository.commit:
      raise SystemExit(
        f"{repository.key} commit mismatch: expected {repository.commit}, got {actual_commit}"
      )
    source = checkout / selected.path
    if not source.is_file():
      raise SystemExit(f"Missing selected Markdown: {repository.key}/{selected.path}")
    target = corpus_root / repository.key / selected.path
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    records.append({
      "repository": repository.key,
      "repository_url": repository.url,
      "commit": repository.commit,
      "license": repository.license_name,
      "relative_path": selected.path,
      "file_sha256": sha256(source),
      "document_id": f"{source.stem}-{sha256(source)[:16]}",
      "category": selected.category,
      "offset_basis": "rag_lab_normalized_markdown_v1",
    })
  manifest = corpus_root / "manifest.jsonl"
  manifest.write_text(
    "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
    encoding="utf-8",
  )
  write_notice(records)
  print(f"documents={len(records)} categories={dict(Counter(r['category'] for r in records))}")
  print(f"manifest={manifest}")


def write_notice(records: list[dict[str, str]]) -> None:
  lines = [
    "# NOTICE — java-interview-real-v1 Sources",
    "",
    "The upstream repositories and downloaded corpus are not committed to `rag-lab`.",
    "Only this provenance manifest, code, derived QA data, and benchmark results are retained.",
    "",
    "## Repositories",
    "",
    "| Repository | URL | Commit | License |",
    "|---|---|---|---|",
  ]
  for repository in REPOSITORIES.values():
    lines.append(
      f"| {repository.key} | {repository.url} | `{repository.commit}` | "
      f"{repository.license_name} |"
    )
  lines.extend([
    "",
    "## Selected Markdown Files",
    "",
    "| Repository | Category | Relative File Path | File SHA-256 |",
    "|---|---|---|---|",
  ])
  for record in records:
    lines.append(
      f"| {record['repository']} | {record['category']} | "
      f"`{record['relative_path']}` | `{record['file_sha256']}` |"
    )
  lines.extend([
    "",
    "The file hashes apply to the unmodified Markdown blobs at the commits above.",
    "Evidence text is an exact `[start_offset, end_offset)` slice of the lab's",
    "`rag_lab_normalized_markdown_v1` representation; normalization only performs",
    "Unicode/line-ending/heading-whitespace cleanup and does not paraphrase body text.",
    "",
  ])
  (ROOT / "NOTICE-SOURCES.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
  main()
