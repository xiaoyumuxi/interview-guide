#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag_lab.common.config import load_config  # noqa: E402
from rag_lab.evaluation.runner import BenchmarkRunner  # noqa: E402


def main() -> None:
  config_path = (
    ROOT / "configs/experiments/qwen-java-interview-real-v1-agent-frozen-test.yaml"
  )
  config = load_config(config_path)
  ledger_path = ROOT / config["test_execution"]["execution_ledger_path"]
  if ledger_path.exists():
    raise SystemExit(f"REFUSED: Test already executed; ledger={ledger_path}")
  logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
  report = BenchmarkRunner(config, ROOT).run()
  dataset_path = ROOT / config["dataset"]["path"]
  raw_path = ROOT / "results/raw" / f"{report['experiment_id']}.json"
  ledger_path.parent.mkdir(parents=True, exist_ok=True)
  ledger = {
    "test_executed": True,
    "execution_kind": "ONE_TIME_AGENT_FROZEN_TEST",
    "experiment_id": report["experiment_id"],
    "executed_at": datetime.now(UTC).isoformat(),
    "dataset_path": config["dataset"]["path"],
    "dataset_sha256": hashlib.sha256(dataset_path.read_bytes()).hexdigest(),
    "freeze_metadata_path": config["test_execution"]["freeze_metadata_path"],
    "raw_result_path": str(raw_path.relative_to(ROOT)),
    "comparison_csv": config["results"]["comparison_csv"],
    "strategies": {
      name: result["metrics"]["Overall"]
      for name, result in report["strategies"].items()
    },
  }
  ledger_path.write_text(
    json.dumps(ledger, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
  )
  print(json.dumps(ledger, ensure_ascii=False, indent=2))


if __name__ == "__main__":
  main()
