#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag_lab.dataset.io import read_jsonl, write_jsonl  # noqa: E402


def main() -> None:
  parser = argparse.ArgumentParser(description="Human-review java-interview-real-v1")
  parser.add_argument("--reviewer", required=True)
  parser.add_argument("--split", choices=["dev", "test"], required=True)
  args = parser.parse_args()
  dataset_dir = ROOT / "data/datasets/java-interview-real-v1"
  pending_path = dataset_dir / f"{args.split}-pending-review.jsonl"
  decisions_path = dataset_dir / f"{args.split}-human-review-decisions.jsonl"
  decisions = load_decisions(decisions_path)
  samples = read_jsonl(pending_path)
  for sample in samples:
    if sample.id in decisions:
      continue
    print("=" * 100)
    print(f"{sample.id} [{sample.type.value}]\nQ: {sample.question}\nA: {sample.reference_answer}")
    for evidence in sample.evidences:
      print(
        f"\nSOURCE: {evidence.metadata.get('repository')}/"
        f"{evidence.metadata.get('relative_path')} "
        f"[{evidence.start_offset},{evidence.end_offset})\n{evidence.text}"
      )
    choice = input("\nApprove? [y]es / [n]o / [q]uit: ").strip().lower()
    if choice == "q":
      break
    approved = choice == "y"
    reason = "" if approved else input("Rejection reason: ").strip()
    decision = {
      "sample_id": sample.id,
      "approved": approved,
      "reason": reason,
      "reviewer": args.reviewer,
      "reviewed_at": datetime.now(UTC).isoformat(),
    }
    append_decision(decisions_path, decision)
    decisions[sample.id] = decision
  approved_ids = {
    sample_id for sample_id, decision in decisions.items() if decision["approved"]
  }
  rejected_ids = {
    sample_id for sample_id, decision in decisions.items() if not decision["approved"]
  }
  if rejected_ids:
    print(f"not frozen: rejected={len(rejected_ids)}; replace rejected items and review again")
    return
  if len(approved_ids) != len(samples):
    print(f"not frozen: approved={len(approved_ids)}/{len(samples)}")
    return
  for sample in samples:
    sample.review_status = f"HUMAN_APPROVED:{args.reviewer}"
  frozen_path = dataset_dir / f"{args.split}.jsonl"
  write_jsonl(frozen_path, samples)
  sha = hashlib.sha256(frozen_path.read_bytes()).hexdigest()
  freeze_metadata = dataset_dir / (
    "FROZEN-TEST.json" if args.split == "test" else "REVIEWED-DEV.json"
  )
  freeze_metadata.write_text(
    json.dumps({
      "dataset": "java-interview-real-v1",
      "split": args.split,
      "count": len(samples),
      "sha256": sha,
      "reviewer": args.reviewer,
      "frozen_at": datetime.now(UTC).isoformat(),
    }, ensure_ascii=False, indent=2),
    encoding="utf-8",
  )
  action = "frozen" if args.split == "test" else "reviewed"
  print(f"{action}={frozen_path} count={len(samples)} sha256={sha}")


def load_decisions(path: Path) -> dict[str, dict[str, object]]:
  if not path.exists():
    return {}
  return {
    decision["sample_id"]: decision
    for decision in (
      json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
      if line.strip()
    )
  }


def append_decision(path: Path, decision: dict[str, object]) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  with path.open("a", encoding="utf-8") as handle:
    handle.write(json.dumps(decision, ensure_ascii=False) + "\n")


if __name__ == "__main__":
  main()
