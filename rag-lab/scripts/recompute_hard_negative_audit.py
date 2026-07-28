#!/usr/bin/env python3
from __future__ import annotations

import json
import copy
import hashlib
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag_lab.chunking import FixedChunker, ParentChildChunker, StructureAwareChunker  # noqa: E402
from rag_lab.chunking.base import embedding_text  # noqa: E402
from rag_lab.common.config import load_config  # noqa: E402
from rag_lab.common.experiment import build_experiment_metadata  # noqa: E402
from rag_lab.common.pipeline import load_documents  # noqa: E402
from rag_lab.dataset.io import read_jsonl  # noqa: E402
from rag_lab.embedding import CachedEmbeddingProvider  # noqa: E402
from rag_lab.evaluation.exports import (  # noqa: E402
  build_hard_negative_rows,
  write_hard_negative_csv,
)
from rag_lab.evaluation.metrics import evaluate_results  # noqa: E402
from rag_lab.evaluation.runner import BenchmarkRunner  # noqa: E402
from rag_lab.retrieval import ExactDenseRetriever  # noqa: E402

DATASETS = {
  "current_dev": (
    "configs/experiments/qwen-java-interview-real-v1-metrics-v2.yaml",
    "results/raw/20260728T092752Z-49193.json",
  ),
  "hard_query_dev": (
    "configs/experiments/qwen-java-interview-hard-dev.yaml",
    "results/raw/20260728T095847Z-52944.json",
  ),
}


def main() -> None:
  reports: dict[str, dict[str, Any]] = {}
  audit: dict[str, Any] = {
    "experiment_id": f"{datetime.now(UTC):%Y%m%dT%H%M%SZ}-hard-negative-audit-fix",
    "timestamp": datetime.now(UTC).isoformat(),
    "test_executed": False,
    "quality_experiment_reexecuted": False,
    "scope": "negative-bearing query ranking statistics only",
    "datasets": {},
  }
  for dataset_name, (config_path, source_raw_path) in DATASETS.items():
    config = load_config(ROOT / config_path)
    source_report = json.loads((ROOT / source_raw_path).read_text())
    metrics = _recompute_dataset(config)
    reports[dataset_name] = {
      "experiment_id": source_report["experiment_id"],
      "strategies": {
        strategy: {"metrics": strategy_metrics}
        for strategy, strategy_metrics in metrics.items()
      },
    }
    audit["datasets"][dataset_name] = {
      "source_quality_experiment_id": source_report["experiment_id"],
      "source_quality_metrics_preserved": True,
      "groups": metrics,
    }
  current_config = load_config(ROOT / DATASETS["current_dev"][0])
  current_path = ROOT / current_config["dataset"]["path"]
  hard_config = load_config(ROOT / DATASETS["hard_query_dev"][0])
  hard_path = ROOT / hard_config["dataset"]["path"]
  metadata = build_experiment_metadata(
    experiment_id=audit["experiment_id"],
    dataset_name="current_dev+hard_query_dev_negative_bearing",
    dataset_path=current_path,
    corpus_manifest_path=ROOT / current_config["corpus"]["manifest_path"],
    embedding_model=current_config["embedding"]["model"],
    embedding_dimensions=current_config["embedding"]["dimensions"],
    tokenizer_model=current_config["tokenizer"]["model"],
    token_count_mode="not_used_for_span_metrics",
    device="cpu",
    document_count=48,
    query_count=35,
    random_seed=current_config["experiment"]["seed"],
    cloud_api_enabled=current_config["cloud"]["enabled"],
    project_root=ROOT,
    timestamp=audit["timestamp"],
  )
  metadata["dataset_sha256"] = hashlib.sha256(
    current_path.read_bytes() + hard_path.read_bytes()
  ).hexdigest()
  audit.update(metadata)
  rows = build_hard_negative_rows(reports)
  write_hard_negative_csv(
    rows,
    ROOT / "results/reports/hard-negative-analysis.csv",
  )
  raw_path = ROOT / "results/raw" / f"{audit['experiment_id']}.json"
  raw_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
  print(f"Wrote {len(rows)} CSV rows and {raw_path}")


def _recompute_dataset(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
  documents = load_documents(
    ROOT / config["corpus"]["raw_dir"],
    ROOT / config["corpus"]["markdown_dir"],
  )
  samples = [
    sample for sample in read_jsonl(ROOT / config["dataset"]["path"])
    if sample.answerable and sample.negative_evidences
  ]
  audit_config = copy.deepcopy(config)
  audit_config["embedding"]["device"] = "cpu"
  provider = CachedEmbeddingProvider(
    BenchmarkRunner(audit_config, ROOT)._provider(),
    ROOT / config["embedding"]["cache_path"],
  )
  strategies = {
    "fixed": FixedChunker(512, 64),
    "structure": StructureAwareChunker(512, True),
    "parent_child": ParentChildChunker(256, True),
  }
  output = {}
  for name, chunker in strategies.items():
    all_chunks = [chunk for document in documents for chunk in chunker.chunk(document)]
    chunks = [chunk for chunk in all_chunks if chunk.metadata.get("indexable", True)]
    embeddings = provider.embed_documents([
      embedding_text(chunk, name != "fixed") for chunk in chunks
    ])
    retriever = ExactDenseRetriever(chunks, embeddings, provider)
    # Full ranking is required only to map every gold/negative evidence to its
    # highest-scoring covering chunk. No general quality aggregate is rerun.
    results = {
      sample.id: retriever.search(sample.question, len(chunks))
      for sample in samples
    }
    metrics = evaluate_results(
      samples,
      results,
      [1, 3, 5, 10],
      coverage_thresholds=[0.25, 0.50, 0.75],
      primary_threshold=0.50,
      any_overlap_threshold=0.01,
    )
    output[name] = {
      group: metrics[group] for group in ("HARD_NEGATIVE", "NEGATIVE_BEARING")
      if group in metrics
    }
  provider.close()
  return output


if __name__ == "__main__":
  main()
