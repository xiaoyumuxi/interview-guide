from __future__ import annotations

import json
from pathlib import Path

from rag_lab.evaluation.workbench import compare_records, load_experiment_records
from rag_lab.generation.runner import prompt_metadata, reference_metrics, render_prompt


def test_prompt_metadata_changes_when_prompt_changes() -> None:
  first = prompt_metadata(
    {"id": "answer", "version": "v1"},
    system_prompt="Use context only.",
    template="Q: {question}\nC: {context}",
  )
  second = prompt_metadata(
    {"id": "answer", "version": "v2"},
    system_prompt="Use context only and be concise.",
    template="Q: {question}\nC: {context}",
  )
  assert first["sha256"] != second["sha256"]
  assert first["version"] == "v1"
  assert second["version"] == "v2"


def test_render_prompt_replaces_question_and_context() -> None:
  rendered = render_prompt(
    "Question={question}\nContext={context}",
    question="What is Redis?",
    context="Redis is an in-memory data store.",
  )
  assert "What is Redis?" in rendered
  assert "in-memory data store" in rendered


def test_reference_metrics_rewards_matching_answer() -> None:
  exact = reference_metrics("Redis supports persistence", "Redis supports persistence")
  partial = reference_metrics("Redis", "Redis supports persistence")
  assert exact["ReferenceTokenF1"] == 1.0
  assert partial["ReferenceTokenF1"] < exact["ReferenceTokenF1"]


def test_workbench_loads_generation_and_retrieval_metrics(tmp_path: Path) -> None:
  report = {
    "experiment_id": "exp-1",
    "timestamp": "2026-08-27T00:00:00Z",
    "dataset_version": "dev-v1",
    "embedding_model": "embed-model",
    "config": {"experiment": {"name": "baseline"}},
    "strategies": {
      "structure": {
        "chunk_count": 10,
        "retrieval_seconds": 0.2,
        "metrics": {"Overall": {"EvidenceRecall@5/50": 0.9}},
        "generation": {
          "provider": {"model": "chat-model"},
          "prompt": {
            "id": "answer",
            "version": "v1",
            "sha256": "abc",
            "system": "system",
            "template": "{question} {context}",
          },
          "metrics": {"Overall": {"JudgeOverall": 4.2}},
        },
      },
    },
  }
  (tmp_path / "exp-1.json").write_text(json.dumps(report), encoding="utf-8")
  records = load_experiment_records(tmp_path)
  assert len(records) == 1
  record = records[0]
  assert record.metrics["EvidenceRecall@5/50"] == 0.9
  assert record.metrics["JudgeOverall"] == 4.2
  assert record.prompt["version"] == "v1"


def test_compare_records_reports_metric_delta(tmp_path: Path) -> None:
  for experiment_id, score, latency in (("base", 0.7, 20.0), ("candidate", 0.8, 18.0)):
    report = {
      "experiment_id": experiment_id,
      "strategies": {
        "fixed": {
          "p95_retrieval_latency_ms": latency,
          "metrics": {"Overall": {"EvidenceRecall@5/50": score}},
        },
      },
    }
    (tmp_path / f"{experiment_id}.json").write_text(json.dumps(report), encoding="utf-8")
  records = {record.experiment_id: record for record in load_experiment_records(tmp_path)}
  rows = {row["metric"]: row for row in compare_records(records["base"], records["candidate"])}
  assert rows["EvidenceRecall@5/50"]["delta"] > 0
  assert rows["EvidenceRecall@5/50"]["direction"] == "higher"
  assert rows["p95_retrieval_latency_ms"]["delta"] < 0
  assert rows["p95_retrieval_latency_ms"]["direction"] == "lower"
