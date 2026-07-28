#!/usr/bin/env python3
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag_lab.chunking import FixedChunker, StructureAwareChunker  # noqa: E402
from rag_lab.chunking.base import embedding_text  # noqa: E402
from rag_lab.common.config import load_config  # noqa: E402
from rag_lab.common.pipeline import load_documents  # noqa: E402
from rag_lab.dataset.io import read_jsonl  # noqa: E402
from rag_lab.embedding import CachedEmbeddingProvider  # noqa: E402
from rag_lab.evaluation.metrics import evidence_coverage, evidence_coverages  # noqa: E402
from rag_lab.evaluation.runner import BenchmarkRunner  # noqa: E402
from rag_lab.retrieval import ExactDenseRetriever, MultiQueryRetriever  # noqa: E402


def main() -> None:
  config = load_config(
    ROOT / "configs/experiments/qwen-java-interview-multisection-ablation.yaml",
  )
  documents = load_documents(
    ROOT / config["corpus"]["raw_dir"],
    ROOT / config["corpus"]["markdown_dir"],
  )
  provider = CachedEmbeddingProvider(
    BenchmarkRunner(config, ROOT)._provider(),
    ROOT / config["embedding"]["cache_path"],
  )
  retrievers = {}
  for name, chunker in {
    "fixed": FixedChunker(512, 64),
    "structure": StructureAwareChunker(512, True),
  }.items():
    chunks = [chunk for document in documents for chunk in chunker.chunk(document)]
    embeddings = provider.embed_documents([
      embedding_text(chunk, name == "structure") for chunk in chunks
    ])
    retrievers[name] = ExactDenseRetriever(chunks, embeddings, provider)

  rows = []
  for dataset_name, dataset_path in {
    "current_dev": "data/datasets/java-interview-real-v1/dev-agent-reviewed.jsonl",
    "hard_dev": "data/datasets/java-interview-real-v1/hard-dev-agent-reviewed.jsonl",
  }.items():
    for sample in read_jsonl(ROOT / dataset_path):
      if not sample.answerable:
        continue
      fixed = retrievers["fixed"].search(sample.question, 10)
      structure = retrievers["structure"].search(sample.question, 10)
      multi = MultiQueryRetriever(retrievers["structure"]).search(sample.question, 10)
      fixed_cov = _coverage(fixed[:5], sample.evidences)
      structure_cov = _coverage(structure[:5], sample.evidences)
      multi_cov = _coverage(multi[:5], sample.evidences)
      cases = []
      if fixed_cov == 1.0 and structure_cov < 1.0:
        cases.append("FIXED_SUCCESS_STRUCTURE_FAIL")
      if structure_cov == 1.0 and fixed_cov < 1.0:
        cases.append("STRUCTURE_SUCCESS_FIXED_FAIL")
      if multi_cov - structure_cov >= 0.25:
        cases.append("MULTI_QUERY_IMPROVE")
      if structure_cov - multi_cov >= 0.25:
        cases.append("MULTI_QUERY_DEGRADE")
      if sample.negative_evidences:
        gold_rank = _first_rank(structure, sample.evidences)
        negative_rank = _first_rank(structure, sample.negative_evidences)
        if gold_rank is None or (
          negative_rank is not None and negative_rank <= gold_rank
        ):
          cases.append("HARD_NEGATIVE_ORDERING_FAIL")
      for case in cases:
        rows.append({
          "dataset": dataset_name,
          "case": case,
          "sample_id": sample.id,
          "question": sample.question,
          "fixed_coverage_at_5": fixed_cov,
          "structure_coverage_at_5": structure_cov,
          "multi_query_coverage_at_5": multi_cov,
          "structure_top_5": "|".join(result.chunk.id for result in structure[:5]),
          "multi_query_top_5": "|".join(result.chunk.id for result in multi[:5]),
        })
  provider.close()
  output = ROOT / "results/reports/failure-case-analysis.csv"
  with output.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
  print(f"Wrote {len(rows)} failure/success cases to {output}")


def _coverage(results: list[object], evidences: list[object]) -> float:
  coverages = evidence_coverages([result.chunk for result in results], evidences)
  return sum(coverage >= 0.50 for coverage in coverages) / len(coverages)


def _first_rank(results: list[object], evidences: list[object]) -> int | None:
  return next(
    (
      result.rank for result in results
      if any(evidence_coverage(result, evidence) >= 0.50 for evidence in evidences)
    ),
    None,
  )


if __name__ == "__main__":
  main()
