#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag_lab.dataset.models import QuerySample  # noqa: E402

QUERY_TYPE_MAP = {
  "IMPLICIT_PARAPHRASE": "PARAPHRASE",
  "SCENARIO_DIAGNOSIS": "PARAPHRASE",
  "CONSTRAINT_BASED_SELECTION": "HARD_NEGATIVE",
  "TERMINOLOGY_DISAMBIGUATION": "TERMINOLOGY",
  "MULTI_SECTION_REASONING": "MULTI_SECTION",
  "CODE_BEHAVIOR": "PARAPHRASE",
  "VERSION_IMPLEMENTATION_DIFFERENCE": "MULTI_SECTION",
  "IMPLEMENTATION_DIFFERENCE": "MULTI_SECTION",
}


def main() -> None:
  dataset_dir = ROOT / "data/datasets/java-interview-real-v1"
  inputs = [
    dataset_dir / "hard-dev-author-a.jsonl",
    dataset_dir / "hard-dev-author-b.jsonl",
  ]
  samples: list[QuerySample] = []
  for path in inputs:
    with path.open(encoding="utf-8") as handle:
      for line in handle:
        if not line.strip():
          continue
        payload = json.loads(line)
        authored_type = payload["type"]
        if authored_type in QUERY_TYPE_MAP:
          payload["validation"].setdefault("hard_dev_type", authored_type)
          mapped_type = QUERY_TYPE_MAP[authored_type]
          if authored_type == "VERSION_IMPLEMENTATION_DIFFERENCE":
            mapped_type = "MULTI_SECTION" if len(payload["evidences"]) > 1 else "PARAPHRASE"
          elif authored_type == "CONSTRAINT_BASED_SELECTION":
            if payload.get("negative_evidences"):
              mapped_type = "HARD_NEGATIVE"
            elif len(payload["evidences"]) > 1:
              mapped_type = "MULTI_SECTION"
            else:
              mapped_type = "PARAPHRASE"
          payload["type"] = mapped_type
        samples.append(QuerySample.model_validate(payload))
  expected_ids = [f"hard_dev_{index:03d}" for index in range(1, 49)]
  actual_ids = [sample.id for sample in samples]
  if actual_ids != expected_ids:
    raise ValueError(f"Hard Dev IDs are not complete and ordered: {actual_ids}")
  output = dataset_dir / "hard-dev-draft.jsonl"
  output.write_text(
    "".join(
      json.dumps(sample.model_dump(mode="json"), ensure_ascii=False) + "\n"
      for sample in samples
    ),
    encoding="utf-8",
  )
  print(f"Wrote {len(samples)} samples to {output}")


if __name__ == "__main__":
  main()
