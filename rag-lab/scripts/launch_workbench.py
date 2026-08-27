#!/usr/bin/env python3
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag_lab.evaluation.workbench import run_workbench  # noqa: E402


def main() -> None:
  parser = argparse.ArgumentParser(description="Launch the local RAG evaluation workbench")
  parser.add_argument(
    "--config",
    type=Path,
    default=None,
    help="Optional experiment config. Required only to run prompt experiments from the UI.",
  )
  parser.add_argument("--host", default="127.0.0.1")
  parser.add_argument("--port", type=int, default=8787)
  parser.add_argument("--no-browser", action="store_true")
  args = parser.parse_args()
  logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
  config_path = args.config.resolve() if args.config else None
  run_workbench(
    project_root=ROOT,
    config_path=config_path,
    host=args.host,
    port=args.port,
    open_browser=not args.no_browser,
  )


if __name__ == "__main__":
  main()
