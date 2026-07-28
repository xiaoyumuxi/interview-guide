#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag_lab.common.pipeline import load_documents  # noqa: E402
from rag_lab.dataset.io import read_jsonl  # noqa: E402

DATASET_DIR = ROOT / "data/datasets/java-interview-real-v1"
EXPECTED_CATEGORIES = {
  "distributed", "java-basics", "java-collections", "juc", "jvm", "message-queue",
  "mysql", "network", "operating-system", "redis", "spring", "system-design",
}


def main() -> None:
  parser = argparse.ArgumentParser(description="Validate Phase 1.5 Hard Dev")
  parser.add_argument(
    "--dataset",
    type=Path,
    default=DATASET_DIR / "hard-dev-agent-reviewed.jsonl",
  )
  args = parser.parse_args()
  errors, summary = validate(args.dataset)
  print(json.dumps(summary, ensure_ascii=False, indent=2))
  if errors:
    for error in errors:
      print(f"ERROR: {error}", file=sys.stderr)
    raise SystemExit(1)


def validate(path: Path) -> tuple[list[str], dict[str, Any]]:
  samples = read_jsonl(path)
  dev = read_jsonl(DATASET_DIR / "dev-agent-reviewed.jsonl")
  test = read_jsonl(DATASET_DIR / "test-agent-reviewed.jsonl")
  documents = {
    document.document_id: document
    for document in load_documents(
      ROOT / "data/corpus/java-interview-real-v1",
      ROOT / "data/markdown/java-interview-real-v1",
    )
  }
  errors: list[str] = []
  dev_evidence = {
    _evidence_key(evidence)
    for sample in dev for evidence in sample.evidences + sample.negative_evidences
  }
  test_evidences = [
    evidence for sample in test
    for evidence in sample.evidences + sample.negative_evidences
  ]
  test_hashes = {_text_hash(evidence.text) for evidence in test_evidences}
  test_sections = {
    (evidence.document_id, tuple(evidence.heading_path)) for evidence in test_evidences
  }
  test_answers = {_normalized(sample.reference_answer) for sample in test}
  test_questions = [_normalized(sample.question) for sample in test]

  categories: Counter[str] = Counter()
  hard_types: Counter[str] = Counter()
  ids: set[str] = set()
  for sample in samples:
    if sample.id in ids:
      errors.append(f"{sample.id}: duplicate id")
    ids.add(sample.id)
    category = str(sample.validation.get("category", ""))
    hard_type = str(sample.validation.get("hard_dev_type", ""))
    categories[category] += 1
    hard_types[hard_type] += 1
    if sample.split != "hard-dev":
      errors.append(f"{sample.id}: split must be hard-dev")
    if sample.generator_model:
      errors.append(f"{sample.id}: generator_model must be null (no runtime model)")
    if not hard_type:
      errors.append(f"{sample.id}: hard_dev_type missing")
    for evidence in sample.evidences + sample.negative_evidences:
      if _evidence_key(evidence) not in dev_evidence:
        errors.append(f"{sample.id}: evidence {evidence.id} is not in Dev evidence pool")
      document = documents.get(evidence.document_id)
      if not document:
        errors.append(f"{sample.id}: missing document {evidence.document_id}")
      elif document.markdown[evidence.start_offset:evidence.end_offset] != evidence.text:
        errors.append(f"{sample.id}: evidence {evidence.id} offset replay failed")
      if _text_hash(evidence.text) in test_hashes:
        errors.append(f"{sample.id}: evidence {evidence.id} content hash leaks Test")
      if (evidence.document_id, tuple(evidence.heading_path)) in test_sections:
        errors.append(f"{sample.id}: evidence {evidence.id} section leaks Test")
      for test_evidence in test_evidences:
        if (
          evidence.document_id == test_evidence.document_id
          and max(evidence.start_offset, test_evidence.start_offset)
          < min(evidence.end_offset, test_evidence.end_offset)
        ):
          errors.append(f"{sample.id}: evidence {evidence.id} span overlaps Test")
          break
    if _normalized(sample.reference_answer) in test_answers:
      errors.append(f"{sample.id}: reference answer exactly reuses Test")
    normalized_question = _normalized(sample.question)
    if any(
      len(normalized_question) >= 12
      and SequenceMatcher(None, normalized_question, test_question).ratio() >= 0.90
      for test_question in test_questions
    ):
      errors.append(f"{sample.id}: question is a near rewrite of Test")

  if len(samples) != 48:
    errors.append(f"expected 48 samples, got {len(samples)}")
  if set(categories) != EXPECTED_CATEGORIES:
    errors.append(f"category set mismatch: {sorted(categories)}")
  for category in EXPECTED_CATEGORIES:
    if categories[category] != 4:
      errors.append(f"{category}: expected 4 samples, got {categories[category]}")

  summary = {
    "dataset": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
    "samples": len(samples),
    "categories": dict(sorted(categories.items())),
    "hard_dev_types": dict(sorted(hard_types.items())),
    "test_execution": "NOT EXECUTED",
    "test_used_for": "READ_ONLY_LEAKAGE_AUDIT",
    "errors": len(errors),
  }
  return errors, summary


def _evidence_key(evidence: Any) -> tuple[str, int, int, str]:
  return (
    evidence.document_id,
    evidence.start_offset,
    evidence.end_offset,
    _text_hash(evidence.text),
  )


def _text_hash(text: str) -> str:
  return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _normalized(text: str) -> str:
  return re.sub(r"\W+", "", text).lower()


if __name__ == "__main__":
  main()
