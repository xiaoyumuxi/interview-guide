#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag_lab.dataset.io import read_jsonl, write_jsonl  # noqa: E402


def sha256(path: Path) -> str:
  return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
  dataset_dir = ROOT / "data/datasets/java-interview-real-v1"
  review_dir = dataset_dir / "agent-review"
  artifacts: dict[str, dict[str, object]] = {}
  for split, expected_count in (("dev", 80), ("test", 40)):
    pending_path = dataset_dir / f"{split}-pending-review.jsonl"
    decisions_path = review_dir / f"{split}-decisions.jsonl"
    samples = read_jsonl(pending_path)
    decisions = [
      json.loads(line)
      for line in decisions_path.read_text(encoding="utf-8").splitlines()
      if line.strip()
    ]
    if len(samples) != expected_count or len(decisions) != expected_count:
      raise SystemExit(
        f"{split}: expected {expected_count} samples and decisions, "
        f"got {len(samples)}/{len(decisions)}"
      )
    decision_by_id = {decision["sample_id"]: decision for decision in decisions}
    if len(decision_by_id) != expected_count:
      raise SystemExit(f"{split}: duplicate decision sample ids")
    sample_ids = {sample.id for sample in samples}
    if set(decision_by_id) != sample_ids:
      raise SystemExit(f"{split}: decisions do not match pending sample ids")
    rejected = [
      decision for decision in decisions if decision.get("approved") is not True
    ]
    if rejected:
      ids = ", ".join(str(decision["sample_id"]) for decision in rejected)
      raise SystemExit(f"{split}: rejected samples must be repaired and re-reviewed: {ids}")
    reviewers = sorted({str(decision["reviewer"]) for decision in decisions})
    for sample in samples:
      decision = decision_by_id[sample.id]
      sample.review_status = f"AGENT_APPROVED:{decision['reviewer']}"
      sample.validation["agent_release_review"] = {
        "reviewer": decision["reviewer"],
        "severity": decision.get("severity", "PASS"),
        "reason": decision.get("reason", ""),
        "review_kind": "SUBAGENT_NOT_HUMAN",
      }
    output_path = dataset_dir / f"{split}-agent-reviewed.jsonl"
    write_jsonl(output_path, samples)
    metadata_path = dataset_dir / f"AGENT-REVIEWED-{split.upper()}.json"
    metadata_path.write_text(
      json.dumps({
        "dataset": "java-interview-real-v1",
        "split": split,
        "count": expected_count,
        "sha256": sha256(output_path),
        "reviewers": reviewers,
        "review_kind": "SUBAGENT_NOT_HUMAN",
        "human_reviewed": False,
        "test_frozen": False,
        "materialized_at": datetime.now(UTC).isoformat(),
      }, ensure_ascii=False, indent=2),
      encoding="utf-8",
    )
    artifacts[split] = {
      "path": str(output_path.relative_to(ROOT)),
      "sha256": sha256(output_path),
      "count": expected_count,
      "decisions_path": str(decisions_path.relative_to(ROOT)),
      "decisions_sha256": sha256(decisions_path),
    }
  dataset_manifest_path = dataset_dir / "dataset-manifest.json"
  dataset_manifest = json.loads(dataset_manifest_path.read_text(encoding="utf-8"))
  dataset_manifest.update({
    "dev_agent_reviewed": True,
    "test_agent_reviewed": True,
    "agent_review_kind": "SUBAGENT_NOT_HUMAN",
    "dev_agent_reviewed_sha256": artifacts["dev"]["sha256"],
    "test_agent_reviewed_sha256": artifacts["test"]["sha256"],
    "dev_human_reviewed": False,
    "test_human_reviewed": False,
    "test_frozen": False,
  })
  dataset_manifest_path.write_text(
    json.dumps(dataset_manifest, ensure_ascii=False, indent=2),
    encoding="utf-8",
  )
  disclaimer_path = review_dir / "AGENT-REVIEW-DISCLAIMER.md"
  disclaimer_path.write_text(
    "# Agent Review Disclaimer\n\n"
    "Dev 80 and Test 40 were reviewed by Codex subagents at the user's request.\n"
    "This is not human review and does not satisfy a requirement for human-labeled gold data.\n"
    "The Test split remains unfrozen: `test_frozen=false`.\n",
    encoding="utf-8",
  )
  release_paths = [
    ROOT / "README.md",
    ROOT / "NOTICE-SOURCES.md",
    ROOT / "docs/PHASE1-REPORT.md",
    ROOT / "docs/INTERVIEW-NOTES.md",
    ROOT / "docs/RESUME-MATERIAL.md",
    ROOT / "configs/experiments/qwen-java-interview-real-v1-agent-reviewed.yaml",
    dataset_manifest_path,
    dataset_dir / "dev-agent-reviewed.jsonl",
    dataset_dir / "test-agent-reviewed.jsonl",
    dataset_dir / "AGENT-REVIEWED-DEV.json",
    dataset_dir / "AGENT-REVIEWED-TEST.json",
    review_dir / "dev-decisions.jsonl",
    review_dir / "test-decisions.jsonl",
    review_dir / "dev-review-report.md",
    review_dir / "test-review-report.md",
    disclaimer_path,
    ROOT / "results/raw/20260728T083734Z-47450.json",
    ROOT / "results/reports/java-interview-real-v1-agent-reviewed.csv",
    ROOT / "results/raw/20260728T065728Z-37412.json",
    ROOT / "results/reports/synthetic-smoke-v1.csv",
  ]
  release_files = {
    str(path.relative_to(ROOT)): {
      "sha256": sha256(path),
      "bytes": path.stat().st_size,
    }
    for path in release_paths
  }
  delivery_path = dataset_dir / "DELIVERY-MANIFEST.json"
  delivery_path.write_text(
    json.dumps({
      "dataset": "java-interview-real-v1",
      "review_kind": "SUBAGENT_NOT_HUMAN",
      "human_reviewed": False,
      "test_frozen": False,
      "artifacts": artifacts,
      "release_files": release_files,
      "disclaimer": {
        "path": str(disclaimer_path.relative_to(ROOT)),
        "sha256": sha256(disclaimer_path),
      },
    }, ensure_ascii=False, indent=2),
    encoding="utf-8",
  )
  print(
    "materialized dev-agent-reviewed=80 test-agent-reviewed=40 "
    "review_kind=SUBAGENT_NOT_HUMAN test_frozen=false"
  )


if __name__ == "__main__":
  main()
