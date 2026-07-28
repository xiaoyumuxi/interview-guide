#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import statistics
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag_lab.chunking import StructureAwareChunker  # noqa: E402
from rag_lab.chunking.base import embedding_text  # noqa: E402
from rag_lab.common.config import load_config  # noqa: E402
from rag_lab.common.experiment import build_experiment_metadata  # noqa: E402
from rag_lab.common.pipeline import load_documents  # noqa: E402
from rag_lab.common.tokenization import build_token_counter  # noqa: E402
from rag_lab.dataset.io import read_jsonl  # noqa: E402
from rag_lab.embedding import CachedEmbeddingProvider  # noqa: E402
from rag_lab.evaluation.metrics import (  # noqa: E402
  evaluate_assembled_contexts,
  evaluate_results,
)
from rag_lab.evaluation.runner import BenchmarkRunner  # noqa: E402
from rag_lab.retrieval import (  # noqa: E402
  ContextAssembler,
  ExactDenseRetriever,
  MultiQueryRetriever,
  MultiSectionQueryDetector,
  RuleBasedChineseQueryDecomposer,
  SectionDiversityReranker,
)
from rag_lab.retrieval.performance import preload_query_cache  # noqa: E402


def main() -> None:
  config_path = (
    Path(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[1] == "--config"
    else ROOT / "configs/experiments/qwen-java-interview-multisection-ablation.yaml"
  )
  config = load_config(config_path)
  run(config)


def run(config: dict[str, Any]) -> dict[str, Any]:
  documents = load_documents(
    ROOT / config["corpus"]["raw_dir"],
    ROOT / config["corpus"]["markdown_dir"],
  )
  chunker = StructureAwareChunker(**config["chunking"]["structure"])
  all_chunks = [chunk for document in documents for chunk in chunker.chunk(document)]
  chunks = [chunk for chunk in all_chunks if chunk.metadata.get("indexable", True)]
  provider = CachedEmbeddingProvider(
    BenchmarkRunner(config, ROOT)._provider(),
    ROOT / config["embedding"]["cache_path"],
  )
  embeddings = provider.embed_documents([embedding_text(chunk, True) for chunk in chunks])
  exact = ExactDenseRetriever(chunks, embeddings, provider)
  timestamp = datetime.now(UTC)
  experiment_id = f"{timestamp:%Y%m%dT%H%M%SZ}-multisection-ablation"
  report: dict[str, Any] = {
    "experiment_id": experiment_id,
    "timestamp": timestamp.isoformat(),
    "embedding_model": provider.model_name,
    "chunk_strategy": "structure",
    "chunk_count": len(chunks),
    "index_size_estimate_bytes": len(chunks) * provider.dimensions * 4,
    "test_executed": False,
    "test_status": "NOT EXECUTED",
    "config": config,
    "datasets": {},
  }
  s2_rankings: dict[str, dict[str, list[Any]]] = {}
  top_ks = config["retrieval"]["top_k"]
  max_k = max(top_ks)
  for dataset_name, dataset_config in config["datasets"].items():
    if "test" in dataset_name.lower() or "test" in Path(dataset_config["path"]).name.lower():
      raise ValueError("Phase 1.5 ablation may not execute Test")
    samples = read_jsonl(ROOT / dataset_config["path"])
    preload_query_cache(provider, _all_query_routes(samples, config))
    dataset_report = {
      "version": dataset_config["version"],
      "sha256": hashlib.sha256((ROOT / dataset_config["path"]).read_bytes()).hexdigest(),
      "samples": len(samples),
      "schemes": {},
    }
    s0_results, s0_cost = _run_exact(samples, exact, max_k, provider)
    dataset_report["schemes"]["S0"] = {
      "retrieval_metrics": _metrics(samples, s0_results, top_ks, config),
      "cost": s0_cost,
      "context_metrics": {},
    }
    for scheme, diversity in (("S1", False), ("S2", True)):
      multi = MultiQueryRetriever(
        exact,
        candidate_top_n=config["multi_query"]["candidate_top_n"],
        max_subqueries=config["multi_query"]["max_subqueries"],
        include_original_query=config["multi_query"]["include_original_query"],
        rrf_k=config["rrf"]["k"],
        diversity_reranker=(
          SectionDiversityReranker(
            config["section_diversity"]["max_chunks_per_section"],
          ) if diversity else None
        ),
      )
      results, cost = _run_multi(samples, multi, max_k, provider)
      dataset_report["schemes"][scheme] = {
        "retrieval_metrics": _metrics(samples, results, top_ks, config),
        "cost": cost,
        "context_metrics": {},
      }
      if scheme == "S2":
        s2_rankings[dataset_name] = results

    assembler = ContextAssembler(
      all_chunks,
      max_tokens=config["context"]["max_tokens"],
      deduplicate=config["context"]["deduplicate"],
      neighbor_expansion=config["context"]["neighbor_expansion"],
      parent_expansion=config["context"]["parent_expansion"],
      max_chunks_per_section=config["section_diversity"]["max_chunks_per_section"],
    )
    contexts = {
      sample.id: {
        k: assembler.assemble(s2_rankings[dataset_name][sample.id][:k])
        for k in top_ks
      }
      for sample in samples if sample.answerable
    }
    s2 = dataset_report["schemes"]["S2"]
    dataset_report["schemes"]["S3"] = {
      # S3 reuses S2 ranking exactly; only assembled context changes.
      "retrieval_metrics": s2["retrieval_metrics"],
      "cost": {
        **s2["cost"],
        "retrieval_reused_from": "S2",
        "additional_query_embeddings": 0,
        "additional_retrieval_calls": 0,
        "approx_average_context_tokens_at_5": statistics.fmean(
          contexts[sample.id][5].tokens for sample in samples if sample.answerable
        ),
      },
      "context_metrics": evaluate_assembled_contexts(samples, contexts, top_ks),
    }
    report["datasets"][dataset_name] = dataset_report
  tokenizer_config = dict(config["tokenizer"])
  tokenizer_config["cache_dir"] = str(ROOT / tokenizer_config["cache_dir"])
  token_counter = build_token_counter(tokenizer_config)
  current_path = ROOT / config["datasets"]["current_dev"]["path"]
  hard_path = ROOT / config["datasets"]["hard_dev"]["path"]
  metadata = build_experiment_metadata(
    experiment_id=experiment_id,
    dataset_name="current_dev+hard_query_dev",
    dataset_path=current_path,
    corpus_manifest_path=ROOT / config["corpus"]["manifest_path"],
    embedding_model=provider.model_name,
    embedding_dimensions=provider.dimensions,
    tokenizer_model=config["tokenizer"]["model"],
    token_count_mode=token_counter.mode,
    device=config["embedding"].get("device") or "cpu/default",
    document_count=len(documents),
    query_count=sum(
      sum(sample.answerable for sample in read_jsonl(ROOT / item["path"]))
      for item in config["datasets"].values()
    ),
    random_seed=config["experiment"]["seed"],
    cloud_api_enabled=config["cloud"]["enabled"],
    project_root=ROOT,
    timestamp=timestamp.isoformat(),
  )
  metadata["dataset_sha256"] = hashlib.sha256(
    current_path.read_bytes() + hard_path.read_bytes()
  ).hexdigest()
  report.update(metadata)
  report["performance_mode"] = "warm_preloaded_query_cache"
  provider.close()
  raw_path = ROOT / "results/raw" / f"{experiment_id}.json"
  raw_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
  _write_ablation_csv(report, ROOT / config["results"]["ablation_csv"])
  _write_context_csv(report, ROOT / config["results"]["context_csv"])
  print(json.dumps(_summary(report), ensure_ascii=False, indent=2))
  return report


def _run_exact(
  samples: list[Any],
  retriever: ExactDenseRetriever,
  top_k: int,
  provider: CachedEmbeddingProvider,
) -> tuple[dict[str, list[Any]], dict[str, Any]]:
  before_hits, before_misses = provider.hits, provider.misses
  before_actual = provider.actual_embedding_count
  results: dict[str, list[Any]] = {}
  latencies: list[float] = []
  for sample in samples:
    if not sample.answerable:
      continue
    started = time.perf_counter()
    results[sample.id] = retriever.search(sample.question, top_k)
    latencies.append(time.perf_counter() - started)
  return results, _cost(
    len(results), 0, len(results), len(results), len(results) * top_k,
    latencies, provider, before_hits, before_misses, before_actual,
  )


def _run_multi(
  samples: list[Any],
  retriever: MultiQueryRetriever,
  top_k: int,
  provider: CachedEmbeddingProvider,
) -> tuple[dict[str, list[Any]], dict[str, Any]]:
  before_hits, before_misses = provider.hits, provider.misses
  before_actual = provider.actual_embedding_count
  results: dict[str, list[Any]] = {}
  latencies: list[float] = []
  for sample in samples:
    if not sample.answerable:
      continue
    started = time.perf_counter()
    results[sample.id] = retriever.search(sample.question, top_k)
    latencies.append(time.perf_counter() - started)
  return results, _cost(
    len(results), retriever.generated_subqueries, retriever.query_embeddings,
    retriever.retrieval_calls, retriever.candidate_results, latencies,
    provider, before_hits, before_misses, before_actual,
  )


def _cost(
  queries: int,
  generated_subqueries: int,
  query_embeddings: int,
  retrieval_calls: int,
  candidate_results: int,
  latencies: list[float],
  provider: CachedEmbeddingProvider,
  before_hits: int,
  before_misses: int,
  before_actual: int,
) -> dict[str, Any]:
  return {
    "queries": queries,
    "generated_subqueries": generated_subqueries,
    "query_embeddings": query_embeddings,
    "cache_hits": provider.hits - before_hits,
    "cache_misses": provider.misses - before_misses,
    "actual_embeddings": provider.actual_embedding_count - before_actual,
    "retrieval_calls": retrieval_calls,
    "average_candidates": candidate_results / queries if queries else 0,
    "p50_retrieval_latency_ms": _percentile(latencies, 0.50) * 1000,
    "p95_retrieval_latency_ms": _percentile(latencies, 0.95) * 1000,
  }


def _metrics(
  samples: list[Any],
  results: dict[str, list[Any]],
  top_ks: list[int],
  config: dict[str, Any],
) -> dict[str, Any]:
  evaluation = config["evaluation"]
  return evaluate_results(
    samples,
    results,
    top_ks,
    coverage_thresholds=evaluation["evidence_coverage_thresholds"],
    primary_threshold=evaluation["primary_coverage_threshold"],
    any_overlap_threshold=evaluation["any_overlap_threshold"],
  )


def _write_ablation_csv(report: dict[str, Any], path: Path) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  metric_names = [
    "EvidenceRecall@5/50", "EvidenceCoverage@5", "AllEvidenceHit@5/50",
    "ContextPrecision@5", "MRR",
  ]
  cost_names = [
    "queries", "generated_subqueries", "query_embeddings", "cache_hits",
    "cache_misses", "actual_embeddings", "retrieval_calls", "average_candidates",
    "p50_retrieval_latency_ms", "p95_retrieval_latency_ms",
  ]
  fields = ["experiment_id", "dataset", "scheme", "group", *metric_names, *cost_names]
  with path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields)
    writer.writeheader()
    for dataset_name, dataset in report["datasets"].items():
      for scheme_name, scheme in dataset["schemes"].items():
        for group, metrics in scheme["retrieval_metrics"].items():
          writer.writerow({
            "experiment_id": report["experiment_id"],
            "dataset": dataset_name,
            "scheme": scheme_name,
            "group": group,
            **{name: metrics.get(name, "") for name in metric_names},
            **{name: scheme["cost"].get(name, "") for name in cost_names},
          })


def _write_context_csv(report: dict[str, Any], path: Path) -> None:
  fields = [
    "experiment_id", "dataset", "scheme", "group", "EvidenceCoverage@5",
    "ContextPrecision@5", "ContextWaste@5", "ApproxContextTokens@5",
  ]
  with path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields)
    writer.writeheader()
    for dataset_name, dataset in report["datasets"].items():
      for scheme_name, scheme in dataset["schemes"].items():
        if scheme_name == "S3":
          groups = scheme["context_metrics"]
          for group, metrics in groups.items():
            writer.writerow({
              "experiment_id": report["experiment_id"],
              "dataset": dataset_name,
              "scheme": scheme_name,
              "group": group,
              "EvidenceCoverage@5": metrics.get("ContextEvidenceCoverage@5", ""),
              "ContextPrecision@5": metrics.get("ContextPrecision@5", ""),
              "ContextWaste@5": metrics.get("ContextWaste@5", ""),
              "ApproxContextTokens@5": metrics.get("ApproxContextTokens@5", ""),
            })
        else:
          for group, metrics in scheme["retrieval_metrics"].items():
            writer.writerow({
              "experiment_id": report["experiment_id"],
              "dataset": dataset_name,
              "scheme": scheme_name,
              "group": group,
              "EvidenceCoverage@5": metrics.get("EvidenceCoverage@5", ""),
              "ContextPrecision@5": metrics.get("ContextPrecision@5", ""),
              "ContextWaste@5": metrics.get("ContextWaste@5", ""),
              "ApproxContextTokens@5": "",
            })


def _summary(report: dict[str, Any]) -> dict[str, Any]:
  return {
    dataset_name: {
      scheme_name: {
        group: {
          key: round(metrics.get(key, 0), 4)
          for key in ("EvidenceRecall@5/50", "EvidenceCoverage@5",
                      "AllEvidenceHit@5/50", "ContextPrecision@5")
        }
        for group, metrics in scheme["retrieval_metrics"].items()
        if group in {"Overall", "MULTI_SECTION"}
      }
      for scheme_name, scheme in dataset["schemes"].items()
    }
    for dataset_name, dataset in report["datasets"].items()
  }


def _percentile(values: list[float], quantile: float) -> float:
  if not values:
    return 0.0
  ordered = sorted(values)
  return ordered[round((len(ordered) - 1) * quantile)]


def _all_query_routes(samples: list[Any], config: dict[str, Any]) -> list[str]:
  detector = MultiSectionQueryDetector()
  decomposer = RuleBasedChineseQueryDecomposer(config["multi_query"]["max_subqueries"])
  queries = []
  for sample in samples:
    if not sample.answerable:
      continue
    queries.append(sample.question)
    if detector.detect(sample.question):
      queries.extend(decomposer.decompose(sample.question))
  return list(dict.fromkeys(queries))


if __name__ == "__main__":
  main()
