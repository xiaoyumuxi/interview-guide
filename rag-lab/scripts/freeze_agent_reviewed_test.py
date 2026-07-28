#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag_lab.release import freeze_agent_reviewed_test  # noqa: E402


def main() -> None:
  dataset_dir = ROOT / "data/datasets/java-interview-real-v1"
  metadata = freeze_agent_reviewed_test(
    source_path=dataset_dir / "test-agent-reviewed.jsonl",
    decisions_path=(
      dataset_dir / "agent-freeze-review/test-final-freeze-decisions.jsonl"
    ),
    output_path=dataset_dir / "test-agent-frozen.jsonl",
    metadata_path=dataset_dir / "AGENT-FROZEN-TEST.json",
    reviewer="final_test_freeze_reviewer",
  )
  print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
  main()
