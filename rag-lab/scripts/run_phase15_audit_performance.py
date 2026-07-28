#!/usr/bin/env python3
from __future__ import annotations

import csv
import copy
import hashlib
import json
import statistics
import sys
import tempfile
import time
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
from rag_lab.common.tokenization import (  # noqa: E402
  LexicalApproxTokenCounter,
  build_token_counter,
  summarize_chunk_tokens,
)
from rag_lab.dataset.io import read_jsonl  # noqa: E402
from rag_lab.embedding import CachedEmbeddingProvider  # noqa: E402
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

SOURCE_ABLATION = ROOT / "results/raw/20260728T100028Z-multisection-ablation.json"


def main() -> None:
  config = load_config(
    ROOT / "configs/experiments/qwen-java-interview-multisection-ablation.yaml",
  )
  documents = load_documents(
    ROOT / config["corpus"]["raw_dir"],
    ROOT / config["corpus"]["markdown_dir"],
  )
  performance_config = copy.deepcopy(config)
  performance_config["embedding"]["device"] = "cpu"
  base_provider = BenchmarkRunner(performance_config, ROOT)._provider()
  structure_chunker = StructureAwareChunker(**config["chunking"]["structure"])
  all_structure_chunks = [
    chunk for document in documents for chunk in structure_chunker.chunk(document)
  ]
  structure_chunks = [
    chunk for chunk in all_structure_chunks if chunk.metadata.get("indexable", True)
  ]
  persistent = CachedEmbeddingProvider(
    base_provider,
    ROOT / config["embedding"]["cache_path"],
  )
  document_embeddings = persistent.embed_documents([
    embedding_text(chunk, True) for chunk in structure_chunks
  ])
  persistent.close()

  tokenizer_config = dict(config["tokenizer"])
  tokenizer_config["cache_dir"] = str(ROOT / tokenizer_config["cache_dir"])
  qwen_counter = build_token_counter(tokenizer_config)
  approximate_counter = LexicalApproxTokenCounter()
  token_rows = _token_comparison(
    documents, approximate_counter, qwen_counter,
  )
  _write_csv(
    ROOT / "results/reports/token-count-comparison.csv",
    token_rows,
    list(token_rows[0]),
  )

  performance: dict[str, list[dict[str, Any]]] = {"cold": [], "warm": []}
  with tempfile.TemporaryDirectory(prefix="rag-lab-phase15-perf-") as temp_dir:
    for dataset_name, dataset_config in config["datasets"].items():
      if "test" in dataset_name.lower() or "test" in Path(dataset_config["path"]).name.lower():
        raise ValueError("Test execution is forbidden")
      samples = [
        sample for sample in read_jsonl(ROOT / dataset_config["path"])
        if sample.answerable
      ]
      warm_queries = _all_query_routes(samples, config)
      for mode in ("cold", "warm"):
        for scheme in ("S0", "S1", "S2", "S3"):
          cache_path = Path(temp_dir) / f"{dataset_name}-{mode}-{scheme}.sqlite3"
          cached = CachedEmbeddingProvider(base_provider, cache_path)
          if mode == "warm":
            preload_query_cache(cached, warm_queries)
          row = _measure_scheme(
            dataset_name,
            samples,
            scheme,
            cached,
            structure_chunks,
            all_structure_chunks,
            document_embeddings,
            config,
            approximate_counter,
            qwen_counter,
          )
          performance[mode].append(row)
          cached.close()
  for mode, rows in performance.items():
    prefixed = [_prefix_performance(row, mode) for row in rows]
    _write_csv(
      ROOT / f"results/reports/ablation-performance-{mode}.csv",
      prefixed,
      list(prefixed[0]),
    )
  updated_raw = _patch_ablation_raw(
    config,
    documents,
    qwen_counter.model_name,
    qwen_counter.mode,
    token_rows,
    performance,
  )
  print(f"Wrote token/performance reports and {updated_raw}")


def _token_comparison(
  documents: list[Any],
  approximate_counter: Any,
  qwen_counter: Any,
) -> list[dict[str, Any]]:
  rows = []
  for name, chunker in {
    "fixed": FixedChunker(512, 64),
    "structure": StructureAwareChunker(512, True),
    "parent_child": ParentChildChunker(256, True),
  }.items():
    chunks = [
      chunk for document in documents for chunk in chunker.chunk(document)
      if chunk.metadata.get("indexable", True)
    ]
    boundaries_before = [
      (chunk.id, chunk.start_offset, chunk.end_offset) for chunk in chunks
    ]
    summary = summarize_chunk_tokens(chunks, approximate_counter, qwen_counter)
    boundaries_after = [
      (chunk.id, chunk.start_offset, chunk.end_offset) for chunk in chunks
    ]
    if boundaries_before != boundaries_after:
      raise AssertionError("Token recount must not change existing chunk boundaries")
    rows.append({
      "strategy": name,
      "chunk_count": len(chunks),
      **summary,
      "chunk_boundaries_changed": False,
    })
  return rows


def _all_query_routes(samples: list[Any], config: dict[str, Any]) -> list[str]:
  detector = MultiSectionQueryDetector()
  decomposer = RuleBasedChineseQueryDecomposer(config["multi_query"]["max_subqueries"])
  queries: list[str] = []
  for sample in samples:
    queries.append(sample.question)
    if detector.detect(sample.question):
      queries.extend(decomposer.decompose(sample.question))
  return list(dict.fromkeys(queries))


def _measure_scheme(
  dataset_name: str,
  samples: list[Any],
  scheme: str,
  provider: CachedEmbeddingProvider,
  chunks: list[Any],
  all_chunks: list[Any],
  document_embeddings: Any,
  config: dict[str, Any],
  approximate_counter: Any,
  qwen_counter: Any,
) -> dict[str, Any]:
  exact = ExactDenseRetriever(chunks, document_embeddings, provider)
  multi = None
  if scheme != "S0":
    multi = MultiQueryRetriever(
      exact,
      candidate_top_n=config["multi_query"]["candidate_top_n"],
      max_subqueries=config["multi_query"]["max_subqueries"],
      include_original_query=config["multi_query"]["include_original_query"],
      rrf_k=config["rrf"]["k"],
      diversity_reranker=(
        SectionDiversityReranker(config["section_diversity"]["max_chunks_per_section"])
        if scheme in {"S2", "S3"} else None
      ),
    )
  assembler = ContextAssembler(
    all_chunks,
    max_tokens=config["context"]["max_tokens"],
    deduplicate=config["context"]["deduplicate"],
    neighbor_expansion=config["context"]["neighbor_expansion"],
    parent_expansion=config["context"]["parent_expansion"],
    max_chunks_per_section=config["section_diversity"]["max_chunks_per_section"],
  ) if scheme == "S3" else None
  before_hits, before_misses = provider.hits, provider.misses
  before_actual = provider.actual_embedding_count
  latencies = []
  contexts = []
  for sample in samples:
    started = time.perf_counter()
    ranked = (
      exact.search(sample.question, 10)
      if multi is None else multi.search(sample.question, 10)
    )
    if assembler is not None:
      contexts.append(assembler.assemble(ranked[:5]))
    latencies.append(time.perf_counter() - started)
  requested_embeddings = len(samples) if multi is None else multi.query_embeddings
  retrieval_calls = len(samples) if multi is None else multi.retrieval_calls
  generated_subqueries = 0 if multi is None else multi.generated_subqueries
  candidate_results = len(samples) * 10 if multi is None else multi.candidate_results
  return {
    "dataset": "hard_query_dev" if dataset_name == "hard_dev" else dataset_name,
    "scheme": scheme,
    "query_count": len(samples),
    "generated_subqueries": generated_subqueries,
    "query_embedding_count": requested_embeddings,
    "cache_hits": provider.hits - before_hits,
    "cache_misses": provider.misses - before_misses,
    "actual_embedding_count": provider.actual_embedding_count - before_actual,
    "retrieval_calls": retrieval_calls,
    "average_candidates": candidate_results / len(samples) if samples else 0.0,
    "p50_latency_ms": _percentile(latencies, 0.50) * 1000,
    "p95_latency_ms": _percentile(latencies, 0.95) * 1000,
    "approx_average_context_tokens": statistics.fmean(
      context.tokens for context in contexts
    ) if contexts else "",
    "qwen_average_context_tokens": statistics.fmean(
      sum(qwen_counter.count(span.text) for span in context.spans)
      for context in contexts
    ) if contexts else "",
    "context_token_budget_mode": "approximate" if contexts else "",
    "test_executed": False,
  }


def _prefix_performance(row: dict[str, Any], mode: str) -> dict[str, Any]:
  identity = {"dataset": row["dataset"], "scheme": row["scheme"]}
  return {
    **identity,
    **{
      f"{mode}_{key}": value
      for key, value in row.items()
      if key not in identity
    },
  }


def _patch_ablation_raw(
  config: dict[str, Any],
  documents: list[Any],
  tokenizer_model: str,
  token_count_mode: str,
  token_rows: list[dict[str, Any]],
  performance: dict[str, list[dict[str, Any]]],
) -> Path:
  source = json.loads(SOURCE_ABLATION.read_text())
  quality_hash = _quality_hash(source)
  timestamp = datetime.now(UTC)
  experiment_id = f"{timestamp:%Y%m%dT%H%M%SZ}-multisection-ablation-audit-fixed"
  current_path = ROOT / config["datasets"]["current_dev"]["path"]
  hard_path = ROOT / config["datasets"]["hard_dev"]["path"]
  metadata = build_experiment_metadata(
    experiment_id=experiment_id,
    dataset_name="current_dev+hard_query_dev",
    dataset_path=current_path,
    corpus_manifest_path=ROOT / config["corpus"]["manifest_path"],
    embedding_model=config["embedding"]["model"],
    embedding_dimensions=config["embedding"]["dimensions"],
    tokenizer_model=config["tokenizer"]["model"],
    token_count_mode=token_count_mode,
    device="cpu",
    document_count=len(documents),
    query_count=121,
    random_seed=config["experiment"]["seed"],
    cloud_api_enabled=config["cloud"]["enabled"],
    project_root=ROOT,
    timestamp=timestamp.isoformat(),
  )
  metadata["dataset_sha256"] = hashlib.sha256(
    current_path.read_bytes() + hard_path.read_bytes()
  ).hexdigest()
  updated = _rename_approximate_token_fields(source)
  updated.update(metadata)
  updated["quality_metrics_source_experiment_id"] = source["experiment_id"]
  updated["quality_metrics_device"] = config["embedding"].get("device") or "cpu/default"
  updated["performance_audit_device"] = "cpu"
  updated["quality_metrics_reexecuted"] = False
  updated["quality_metrics_sha256"] = quality_hash
  updated["token_count_comparison"] = token_rows
  updated["performance_audit"] = performance
  updated["test_status"] = "NOT EXECUTED"
  if _quality_hash(updated) != quality_hash:
    raise AssertionError("Audit patch changed existing quality metrics")
  output = ROOT / "results/raw" / f"{experiment_id}.json"
  output.write_text(json.dumps(updated, ensure_ascii=False, indent=2), encoding="utf-8")
  return output


def _rename_approximate_token_fields(value: Any) -> Any:
  if isinstance(value, dict):
    renamed = {}
    for key, item in value.items():
      new_key = key
      if key.startswith("ContextTokens@"):
        new_key = key.replace("ContextTokens@", "ApproxContextTokens@", 1)
      elif key == "average_context_tokens_at_5":
        new_key = "approx_average_context_tokens_at_5"
      renamed[new_key] = _rename_approximate_token_fields(item)
    return renamed
  if isinstance(value, list):
    return [_rename_approximate_token_fields(item) for item in value]
  return value


def _quality_hash(report: dict[str, Any]) -> str:
  quality = {}
  for dataset_name, dataset in report.get("datasets", {}).items():
    quality[dataset_name] = {}
    for scheme_name, scheme in dataset.get("schemes", {}).items():
      context_metrics = {
        group: {
          key: value for key, value in metrics.items()
          if "Tokens@" not in key
        }
        for group, metrics in scheme.get("context_metrics", {}).items()
      }
      quality[dataset_name][scheme_name] = {
        "retrieval_metrics": scheme.get("retrieval_metrics", {}),
        "context_metrics": context_metrics,
      }
  payload = json.dumps(quality, sort_keys=True, separators=(",", ":"))
  return hashlib.sha256(payload.encode()).hexdigest()


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  with path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)


def _percentile(values: list[float], quantile: float) -> float:
  if not values:
    return 0.0
  ordered = sorted(values)
  return ordered[round((len(ordered) - 1) * quantile)]


if __name__ == "__main__":
  main()
