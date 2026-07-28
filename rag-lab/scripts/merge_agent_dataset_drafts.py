#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag_lab.common.pipeline import load_documents  # noqa: E402
from rag_lab.dataset.io import read_jsonl, write_jsonl  # noqa: E402
from rag_lab.dataset.java_real_builder import (  # noqa: E402
  exact_stratified_pending_split,
  greedy_deduplicate_and_select,
  validate_extractive_grounding,
)
from rag_lab.dataset.validator import DatasetValidator  # noqa: E402
from rag_lab.embedding import (  # noqa: E402
  CachedEmbeddingProvider,
  SentenceTransformerEmbeddingProvider,
)


def sha256(path: Path) -> str:
  return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
  parser = argparse.ArgumentParser(description="Merge and validate agent-authored Java QA drafts")
  parser.add_argument("--device", default="mps")
  parser.add_argument("--dedup-threshold", type=float, default=0.90)
  args = parser.parse_args()
  dataset_dir = ROOT / "data/datasets/java-interview-real-v1"
  draft_dir = dataset_dir / "agent-drafts"
  drafts = [
    *read_jsonl(draft_dir / "single.jsonl"),
    *read_jsonl(draft_dir / "relations.jsonl"),
  ]
  if len(drafts) != 180:
    raise SystemExit(f"Expected 180 drafts, got {len(drafts)}")
  for index, sample in enumerate(drafts, start=1):
    previous_id = sample.id
    sample.id = f"java_real_candidate_{index:03d}"
    sample.validation["draft_id"] = previous_id
  documents = load_documents(
    ROOT / "data/corpus/java-interview-real-v1",
    ROOT / "data/markdown/java-interview-real-v1",
  )
  document_by_id = {document.document_id: document for document in documents}
  for sample in drafts:
    for evidence in [*sample.evidences, *sample.negative_evidences]:
      document = document_by_id.get(evidence.document_id)
      if document is not None:
        evidence.text = document.markdown[evidence.start_offset:evidence.end_offset]
        evidence.metadata["offset_basis"] = "rag_lab_normalized_markdown_v1"
  errors = DatasetValidator().validate(drafts, document_by_id)
  if errors:
    raise SystemExit("Draft validation failed:\n" + "\n".join(errors[:80]))
  distribution = Counter(sample.type.value for sample in drafts)
  expected = {
    "DIRECT_FACT": 50,
    "PARAPHRASE": 40,
    "TERMINOLOGY": 25,
    "MULTI_SECTION": 25,
    "HARD_NEGATIVE": 25,
    "UNANSWERABLE": 15,
  }
  if dict(distribution) != expected:
    raise SystemExit(f"Draft distribution mismatch: {dict(distribution)}")
  extractive_errors = validate_extractive_grounding(drafts)
  if extractive_errors:
    raise SystemExit(
      "Draft grounding validation failed:\n" + "\n".join(extractive_errors[:80])
    )
  write_jsonl(dataset_dir / "candidates.jsonl", drafts)
  embedding = CachedEmbeddingProvider(
    SentenceTransformerEmbeddingProvider(
      model_name="Qwen/Qwen3-Embedding-0.6B",
      dimensions=1024,
      device=args.device,
      batch_size=16,
      local_files_only=True,
      cache_folder=str(ROOT / "data/cache/models"),
    ),
    ROOT / "data/cache/embeddings-java-interview-real-dedup.sqlite3",
  )
  vectors = embedding.embed_queries([sample.question for sample in drafts])
  selected = greedy_deduplicate_and_select(drafts, vectors, args.dedup_threshold)
  embedding.close()
  dev_pending, test_pending = exact_stratified_pending_split(selected)
  write_jsonl(dataset_dir / "all-pending-review.jsonl", selected)
  write_jsonl(dataset_dir / "dev-pending-review.jsonl", dev_pending)
  write_jsonl(dataset_dir / "test-pending-review.jsonl", test_pending)
  write_review_packet(dataset_dir / "DEV-REVIEW.md", dev_pending, "Dev")
  write_review_packet(dataset_dir / "TEST-REVIEW.md", test_pending, "Test")
  source_manifest = ROOT / "data/corpus/java-interview-real-v1/manifest.jsonl"
  source_records = [
    json.loads(line)
    for line in source_manifest.read_text(encoding="utf-8").splitlines()
    if line
  ]
  manifest = {
    "dataset": "java-interview-real-v1",
    "source_document_count": len(source_records),
    "source_repositories": {
      record["repository"]: {
        "repository_url": record["repository_url"],
        "commit": record["commit"],
        "license": record["license"],
      }
      for record in source_records
    },
    "offset_basis": "rag_lab_normalized_markdown_v1",
    "candidate_count": len(drafts),
    "selected_count": len(selected),
    "dev_pending_human_review_count": len(dev_pending),
    "test_pending_human_review_count": len(test_pending),
    "selected_type_counts": dict(Counter(sample.type.value for sample in selected)),
    "selected_category_counts": category_counts(selected),
    "dev_category_counts": category_counts(dev_pending),
    "test_category_counts": category_counts(test_pending),
    "selected_repository_counts": repository_counts(selected),
    "dev_repository_counts": repository_counts(dev_pending),
    "test_repository_counts": repository_counts(test_pending),
    "embedded_negative_evidence_count": sum(
      len(sample.negative_evidences) for sample in selected
    ),
    "dev_test_evidence_or_section_leakage": False,
    "question_generation_model": None,
    "embedding_model": "Qwen/Qwen3-Embedding-0.6B",
    "embedding_model_purpose": "semantic_deduplication_only",
    "dedup_threshold": args.dedup_threshold,
    "source_manifest_sha256": sha256(source_manifest),
    "notice_sources_sha256": sha256(ROOT / "NOTICE-SOURCES.md"),
    "candidate_sha256": sha256(dataset_dir / "candidates.jsonl"),
    "selected_pending_sha256": sha256(dataset_dir / "all-pending-review.jsonl"),
    "dev_pending_sha256": sha256(dataset_dir / "dev-pending-review.jsonl"),
    "test_pending_sha256": sha256(dataset_dir / "test-pending-review.jsonl"),
    "dev_human_reviewed": False,
    "test_human_reviewed": False,
    "test_frozen": False,
  }
  (dataset_dir / "dataset-manifest.json").write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2),
    encoding="utf-8",
  )
  print(
    f"candidates={len(drafts)} selected={len(selected)} "
    f"dev_pending={len(dev_pending)} test_pending={len(test_pending)}"
  )
  print(f"selected_types={dict(Counter(sample.type.value for sample in selected))}")


def category_counts(samples: list[object]) -> dict[str, int]:
  return dict(sorted(Counter(
    evidence.metadata.get("category", "unknown")
    for sample in samples
    for evidence in sample.evidences
  ).items()))


def repository_counts(samples: list[object]) -> dict[str, int]:
  return dict(sorted(Counter(
    evidence.metadata.get("repository", "unknown")
    for sample in samples
    for evidence in sample.evidences
  ).items()))


def write_review_packet(path: Path, samples: list[object], split_name: str) -> None:
  lines = [
    f"# java-interview-real-v1 — {split_name} Human Review",
    "",
    "Each item must be approved by a human before the reviewed JSONL is created.",
    "",
  ]
  for index, sample in enumerate(samples, start=1):
    lines.extend([
      f"## {index}. {sample.id} — {sample.type.value}",
      "",
      "- [ ] Evidence offsets replay exactly",
      "- [ ] Question sounds like a real Java backend interview",
      "- [ ] Answer is concise, grounded, and adds no external fact",
      "- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)",
      "",
      f"**Question:** {sample.question}",
      "",
      f"**Reference Answer:** {sample.reference_answer}",
      "",
    ])
    for evidence_index, evidence in enumerate(sample.evidences, start=1):
      lines.extend([
        f"**Evidence {evidence_index}:** "
        f"`{evidence.metadata.get('repository')}/{evidence.metadata.get('relative_path')}` "
        f"offset `[{evidence.start_offset}, {evidence.end_offset})`",
        "",
        evidence.text,
        "",
      ])
    for evidence_index, evidence in enumerate(sample.negative_evidences, start=1):
      lines.extend([
        f"**Hard Negative {evidence_index}:** "
        f"`{evidence.metadata.get('repository')}/{evidence.metadata.get('relative_path')}` "
        f"offset `[{evidence.start_offset}, {evidence.end_offset})`",
        "",
        evidence.text,
        "",
      ])
  path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
  main()
