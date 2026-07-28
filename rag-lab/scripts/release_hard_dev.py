#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag_lab.dataset.io import read_jsonl  # noqa: E402


def main() -> None:
  dataset_dir = ROOT / "data/datasets/java-interview-real-v1"
  review_dir = dataset_dir / "hard-dev-review"
  decision_paths = [
    review_dir / "review-decisions.jsonl",
    review_dir / "rereview-decisions.jsonl",
    review_dir / "final-rereview-decisions.jsonl",
  ]
  latest: dict[str, dict[str, Any]] = {}
  history: dict[str, list[str]] = {}
  for path in decision_paths:
    with path.open(encoding="utf-8") as handle:
      for line in handle:
        decision = json.loads(line)
        sample_id = decision["sample_id"]
        latest[sample_id] = decision
        history.setdefault(sample_id, []).append(decision["decision"])

  samples = read_jsonl(dataset_dir / "hard-dev-draft.jsonl")
  missing = [sample.id for sample in samples if sample.id not in latest]
  rejected = [
    sample.id for sample in samples
    if latest.get(sample.id, {}).get("decision") != "APPROVE"
  ]
  if missing or rejected:
    raise ValueError(f"Hard Dev cannot be released; missing={missing}, rejected={rejected}")

  output = dataset_dir / "hard-dev-agent-reviewed.jsonl"
  output.write_text(
    "".join(
      json.dumps(
        sample.model_copy(update={
          "review_status": "AGENT_REVIEWED_NOT_HUMAN",
          "validation": {
            **sample.validation,
            "review_kind": "AGENT_REVIEWED_NOT_HUMAN",
            "review_history": history[sample.id],
          },
        }).model_dump(mode="json"),
        ensure_ascii=False,
      ) + "\n"
      for sample in samples
    ),
    encoding="utf-8",
  )
  final_decisions = review_dir / "final-decisions.jsonl"
  final_decisions.write_text(
    "".join(
      json.dumps({
        **latest[sample.id],
        "decision": "APPROVE",
        "review_kind": "AGENT_REVIEWED_NOT_HUMAN",
        "decision_history": history[sample.id],
      }, ensure_ascii=False) + "\n"
      for sample in samples
    ),
    encoding="utf-8",
  )
  digest = hashlib.sha256(output.read_bytes()).hexdigest()
  (dataset_dir / "AGENT-REVIEWED-HARD-DEV.json").write_text(
    json.dumps({
      "dataset": "java-interview-real-v1-hard-dev-agent-reviewed",
      "samples": len(samples),
      "review_kind": "AGENT_REVIEWED_NOT_HUMAN",
      "human_reviewed": False,
      "test_executed": False,
      "test_status": "NOT EXECUTED",
      "sha256": digest,
    }, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
  )
  print(f"Released {len(samples)} agent-reviewed samples; sha256={digest}")


if __name__ == "__main__":
  main()
