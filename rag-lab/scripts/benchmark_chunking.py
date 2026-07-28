#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag_lab.common.config import load_config  # noqa: E402
from rag_lab.evaluation.runner import BenchmarkRunner  # noqa: E402


def main() -> None:
  parser = argparse.ArgumentParser(description="Benchmark Phase 1 chunking strategies")
  parser.add_argument("--config", type=Path, default=ROOT / "configs/baseline.yaml")
  args = parser.parse_args()
  logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
  report = BenchmarkRunner(load_config(args.config), ROOT).run()
  summary = {
    name: {
      "EvidenceRecall@5/50": result["metrics"]["Overall"]["EvidenceRecall@5/50"],
      "EvidenceCoverage@5": result["metrics"]["Overall"]["EvidenceCoverage@5"],
      "ContextPrecision@5": result["metrics"]["Overall"]["ContextPrecision@5"],
      "MRR": result["metrics"]["Overall"]["MRR"],
      "chunks": result["chunk_count"],
    }
    for name, result in report["strategies"].items()
  }
  print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
  main()
