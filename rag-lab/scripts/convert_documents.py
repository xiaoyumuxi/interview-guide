#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag_lab.common.pipeline import load_documents  # noqa: E402


def main() -> None:
  parser = argparse.ArgumentParser(description="Convert source documents to normalized Markdown")
  parser.add_argument("--input", type=Path, default=ROOT / "data/raw")
  parser.add_argument("--output", type=Path, default=ROOT / "data/markdown")
  args = parser.parse_args()
  documents = load_documents(args.input, args.output)
  print(f"converted={len(documents)} output={args.output}")


if __name__ == "__main__":
  main()

