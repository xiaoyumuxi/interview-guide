#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag_lab.evaluation.exports import (  # noqa: E402
  build_hard_negative_rows,
  write_hard_negative_csv,
)

def main() -> None:
  audit_paths = sorted((ROOT / "results/raw").glob("*-hard-negative-audit-fix.json"))
  if not audit_paths:
    raise FileNotFoundError("Run scripts/recompute_hard_negative_audit.py first")
  audit = json.loads(audit_paths[-1].read_text())
  reports = {}
  for dataset_name, dataset in audit["datasets"].items():
    reports[dataset_name] = {
      "experiment_id": dataset["source_quality_experiment_id"],
      "strategies": {
        strategy: {"metrics": groups}
        for strategy, groups in dataset["groups"].items()
      },
    }
  rows = build_hard_negative_rows(reports)
  output = ROOT / "results/reports/hard-negative-analysis.csv"
  write_hard_negative_csv(rows, output)
  identity_fields = ("experiment_id", "dataset", "strategy", "group")
  if any(not row[field] for row in rows for field in identity_fields):
    raise ValueError("Hard-negative CSV identity fields must not be empty")
  print(f"Wrote {len(rows)} rows to {output}")


if __name__ == "__main__":
  main()
