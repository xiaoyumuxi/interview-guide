#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag_lab.common.pipeline import load_documents  # noqa: E402
from rag_lab.dataset.io import read_jsonl  # noqa: E402
from rag_lab.dataset.java_real_builder import validate_extractive_grounding  # noqa: E402
from rag_lab.dataset.models import QueryType  # noqa: E402
from rag_lab.dataset.validator import DatasetValidator  # noqa: E402

EXPECTED_CATEGORIES = {
  "java-basics",
  "java-collections",
  "juc",
  "jvm",
  "spring",
  "mysql",
  "redis",
  "network",
  "operating-system",
  "distributed",
  "message-queue",
  "system-design",
}
EXCLUDED_PATHS = {
  "docs/system-design/framework/spring/springboot-knowledge-and-questions-summary.md",
  "docs/database/redis/redis-cluster.md",
  "docs/distributed-system/distributed-system-interview-questions.md",
}


def main() -> None:
  dataset_dir = ROOT / "data/datasets/java-interview-real-v1"
  candidates = read_jsonl(dataset_dir / "candidates.jsonl")
  selected = read_jsonl(dataset_dir / "all-pending-review.jsonl")
  dev = read_jsonl(dataset_dir / "dev-pending-review.jsonl")
  test = read_jsonl(dataset_dir / "test-pending-review.jsonl")
  documents = load_documents(
    ROOT / "data/corpus/java-interview-real-v1",
    ROOT / "data/markdown/java-interview-real-v1",
  )
  document_by_id = {document.document_id: document for document in documents}
  errors = []
  if (len(candidates), len(selected), len(dev), len(test)) != (180, 120, 80, 40):
    errors.append("dataset counts are not 180/120/80/40")
  errors.extend(DatasetValidator().validate(candidates, document_by_id))
  errors.extend(validate_extractive_grounding(candidates))
  for split_name, expected_count in (("dev", 80), ("test", 40)):
    agent_path = dataset_dir / f"{split_name}-agent-reviewed.jsonl"
    if agent_path.exists():
      agent_samples = read_jsonl(agent_path)
      if len(agent_samples) != expected_count:
        errors.append(f"{split_name} agent-reviewed count mismatch")
      if any(
        not sample.review_status.startswith("AGENT_APPROVED:")
        for sample in agent_samples
      ):
        errors.append(f"{split_name} contains a non-approved agent review status")
      errors.extend(DatasetValidator().validate(agent_samples, document_by_id))
      errors.extend(validate_extractive_grounding(agent_samples))
  expected_types = {
    "DIRECT_FACT": 32,
    "PARAPHRASE": 28,
    "TERMINOLOGY": 18,
    "MULTI_SECTION": 18,
    "HARD_NEGATIVE": 14,
    "UNANSWERABLE": 10,
  }
  if dict(Counter(sample.type.value for sample in selected)) != expected_types:
    errors.append("selected type distribution mismatch")
  selected_ids = {sample.id for sample in selected}
  if selected_ids != {sample.id for sample in [*dev, *test]}:
    errors.append("selected rows do not equal dev + test")
  if {sample.id for sample in dev} & {sample.id for sample in test}:
    errors.append("dev/test sample id overlap")
  if any(sample.review_status != "PENDING_HUMAN" for sample in selected):
    errors.append("selected rows must remain PENDING_HUMAN")
  categories = {
    evidence.metadata.get("category")
    for sample in selected
    for evidence in sample.evidences
  }
  if categories != EXPECTED_CATEGORIES:
    errors.append(f"selected category coverage mismatch: {sorted(categories)}")
  for split_name, split_samples in (("dev", dev), ("test", test)):
    split_categories = {
      evidence.metadata.get("category")
      for sample in split_samples
      for evidence in sample.evidences
    }
    if split_categories != EXPECTED_CATEGORIES:
      errors.append(
        f"{split_name} category coverage mismatch: {sorted(split_categories)}"
      )
    if not any(
      evidence.metadata.get("repository") == "advanced-java"
      for sample in split_samples
      for evidence in sample.evidences
    ):
      errors.append(f"{split_name} has no advanced-java evidence")
  source_manifest = [
    json.loads(line)
    for line in (
      ROOT / "data/corpus/java-interview-real-v1/manifest.jsonl"
    ).read_text(encoding="utf-8").splitlines()
    if line
  ]
  if not 40 <= len(source_manifest) <= 60:
    errors.append(f"source manifest must contain 40-60 files, got {len(source_manifest)}")
  selected_paths = {record["relative_path"] for record in source_manifest}
  if selected_paths & EXCLUDED_PATHS:
    errors.append("source manifest contains an excluded navigation/promotion document")
  for sample in candidates:
    if sample.generator_model is not None:
      errors.append(f"{sample.id}: generator_model must be null")
    if sample.answerable and any(
      sample.reference_answer.strip() == evidence.text.strip()
      for evidence in sample.evidences
    ):
      errors.append(f"{sample.id}: reference answer copies the complete evidence")
    if sample.type == QueryType.HARD_NEGATIVE:
      if len(sample.negative_evidences) != 2:
        errors.append(f"{sample.id}: hard negative must embed exactly two negative evidences")
      if sample.negative_evidence_ids != [
        evidence.id for evidence in sample.negative_evidences
      ]:
        errors.append(f"{sample.id}: negative evidence ids are not self-contained")
  leakage = split_leakage(dev, test)
  errors.extend(leakage)
  if errors:
    raise SystemExit("java-interview-real-v1 validation failed:\n" + "\n".join(errors[:100]))
  gold_count = sum(len(sample.evidences) for sample in selected)
  negative_count = sum(len(sample.negative_evidences) for sample in selected)
  print(
    f"PASS candidates=180 selected=120 dev=80 test=40 sources={len(source_manifest)} "
    f"categories=12 gold_evidence={gold_count} negative_evidence={negative_count} "
    "split_leakage=0 generator_models=0"
  )


def split_leakage(dev: list[object], test: list[object]) -> list[str]:
  def keys(samples: list[object]) -> set[tuple[object, ...]]:
    output = set()
    for sample in samples:
      for evidence in [*sample.evidences, *sample.negative_evidences]:
        output.add(("evidence", evidence.id))
        output.add(("section", evidence.document_id, *evidence.heading_path))
    return output

  overlap = keys(dev) & keys(test)
  return [f"dev/test evidence or section leakage: {len(overlap)} keys"] if overlap else []


if __name__ == "__main__":
  main()
