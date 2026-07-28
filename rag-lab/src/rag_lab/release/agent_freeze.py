from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from rag_lab.dataset.io import read_jsonl, write_jsonl


def validate_agent_freeze_decisions(
  sample_ids: list[str],
  decisions: list[dict[str, Any]],
) -> None:
  by_id: dict[str, dict[str, Any]] = {}
  for decision in decisions:
    sample_id = str(decision["sample_id"])
    if sample_id in by_id:
      raise ValueError(f"duplicate decision: {sample_id}")
    by_id[sample_id] = decision
  missing = sorted(set(sample_ids) - by_id.keys())
  extra = sorted(by_id.keys() - set(sample_ids))
  rejected = sorted(
    sample_id for sample_id in sample_ids
    if by_id.get(sample_id, {}).get("decision") != "APPROVE"
  )
  if missing or extra or rejected:
    raise ValueError(
      f"agent freeze decisions not approved: missing={missing}, extra={extra}, "
      f"not approved={rejected}",
    )
  if any(
    by_id[sample_id].get("review_kind") != "AGENT_REVIEWED_NOT_HUMAN"
    for sample_id in sample_ids
  ):
    raise ValueError("all decisions must declare AGENT_REVIEWED_NOT_HUMAN")


def freeze_agent_reviewed_test(
  *,
  source_path: Path,
  decisions_path: Path,
  output_path: Path,
  metadata_path: Path,
  reviewer: str,
) -> dict[str, Any]:
  samples = read_jsonl(source_path)
  decisions = [
    json.loads(line)
    for line in decisions_path.read_text(encoding="utf-8").splitlines()
    if line.strip()
  ]
  validate_agent_freeze_decisions([sample.id for sample in samples], decisions)
  for sample in samples:
    sample.review_status = f"AGENT_FROZEN_APPROVED:{reviewer}"
    sample.validation = {
      **sample.validation,
      "freeze_review_kind": "AGENT_REVIEWED_NOT_HUMAN",
      "freeze_reviewer": reviewer,
    }
  write_jsonl(output_path, samples)
  metadata = {
    "dataset": "java-interview-real-v1",
    "split": "test",
    "count": len(samples),
    "sha256": hashlib.sha256(output_path.read_bytes()).hexdigest(),
    "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
    "decisions_sha256": hashlib.sha256(decisions_path.read_bytes()).hexdigest(),
    "reviewer": reviewer,
    "freeze_kind": "AGENT_REVIEWED_NOT_HUMAN",
    "human_reviewed": False,
    "frozen": True,
    "test_executed": False,
    "frozen_at": datetime.now(UTC).isoformat(),
  }
  metadata_path.write_text(
    json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
  )
  return metadata
