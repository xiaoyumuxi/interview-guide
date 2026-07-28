from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from rag_lab.evaluation.runner import BenchmarkRunner
from rag_lab.release.agent_freeze import validate_agent_freeze_decisions


def test_agent_freeze_requires_all_approvals() -> None:
  decisions = [
    {"sample_id": "q1", "decision": "APPROVE"},
    {"sample_id": "q2", "decision": "REJECT"},
  ]
  with pytest.raises(ValueError, match="not approved"):
    validate_agent_freeze_decisions(["q1", "q2"], decisions)


def test_authorized_agent_frozen_test_can_run_once(tmp_path: Path) -> None:
  dataset = tmp_path / "test-agent-frozen.jsonl"
  dataset.write_text("".join(f'{{"id":"q{index}"}}\n' for index in range(40)))
  dataset_sha = hashlib.sha256(dataset.read_bytes()).hexdigest()
  freeze = tmp_path / "AGENT-FROZEN-TEST.json"
  freeze.write_text(json.dumps({
    "count": 40,
    "sha256": dataset_sha,
    "frozen": True,
    "freeze_kind": "AGENT_REVIEWED_NOT_HUMAN",
    "human_reviewed": False,
  }))
  ledger = tmp_path / "execution.json"
  runner = BenchmarkRunner(
    {
      "dataset": {
        "path": dataset.name,
        "version": "java-interview-real-v1-agent-frozen-test",
      },
      "test_execution": {
        "allow_agent_frozen_test_once": True,
        "freeze_metadata_path": freeze.name,
        "execution_ledger_path": ledger.name,
      },
    },
    tmp_path,
  )
  runner._assert_not_test_dataset()
  assert runner.is_test_execution is True
  ledger.write_text("{}")
  with pytest.raises(ValueError, match="already been executed"):
    runner._assert_not_test_dataset()
