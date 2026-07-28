from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from rag_lab.dataset.models import QuerySample


def write_jsonl(path: Path, samples: Iterable[QuerySample]) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  with path.open("w", encoding="utf-8") as handle:
    for sample in samples:
      handle.write(sample.model_dump_json() + "\n")


def read_jsonl(path: Path) -> list[QuerySample]:
  with path.open(encoding="utf-8") as handle:
    return [QuerySample.model_validate(json.loads(line)) for line in handle if line.strip()]

