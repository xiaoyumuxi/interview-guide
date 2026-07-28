#!/usr/bin/env python3
from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag_lab.dataset.io import read_jsonl  # noqa: E402


def main() -> None:
  parser = argparse.ArgumentParser(description="Inspect dataset samples")
  parser.add_argument("--dataset", type=Path, default=ROOT / "data/datasets/dev.jsonl")
  parser.add_argument("--type")
  parser.add_argument("--sample", type=int, default=5)
  parser.add_argument("--seed", type=int, default=42)
  args = parser.parse_args()
  samples = read_jsonl(args.dataset)
  if args.type:
    samples = [sample for sample in samples if sample.type.value == args.type.upper()]
  selected = random.Random(args.seed).sample(samples, min(args.sample, len(samples)))
  for sample in selected:
    print("=" * 88)
    print(f"{sample.id}  type={sample.type.value}  split={sample.split}")
    print(f"Question: {sample.question}")
    print(f"Answer: {sample.reference_answer}")
    for evidence in sample.evidences:
      print(
        f"Evidence: document={evidence.document_id} "
        f"offset=[{evidence.start_offset},{evidence.end_offset}) "
        f"heading={' > '.join(evidence.heading_path)}"
      )
      print(evidence.text)


if __name__ == "__main__":
  main()

