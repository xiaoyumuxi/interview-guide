from __future__ import annotations

import csv
import hashlib
import json
import logging
import os
import platform
import statistics
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from rag_lab.chunking import FixedChunker, ParentChildChunker, StructureAwareChunker
from rag_lab.chunking.base import embedding_text
from rag_lab.common.pipeline import load_documents
from rag_lab.common.experiment import build_experiment_metadata
from rag_lab.common.tokenization import (
  LexicalApproxTokenCounter,
  TokenCounter,
  build_token_counter,
  summarize_chunk_tokens,
)
from rag_lab.dataset.io import read_jsonl
from rag_lab.embedding import (
  CachedEmbeddingProvider,
  HashingEmbeddingProvider,
  SentenceTransformerEmbeddingProvider,
)
from rag_lab.evaluation.metrics import evaluate_results
from rag_lab.models import DocumentChunk
from rag_lab.retrieval import ExactDenseRetriever

LOGGER = logging.getLogger(__name__)


class BenchmarkRunner:
  def __init__(self, config: dict[str, Any], project_root: Path) -> None:
    self.config = config
    self.root = project_root
    self.approximate_token_counter: TokenCounter = LexicalApproxTokenCounter()
    self.qwen_token_counter: TokenCounter = self.approximate_token_counter
    self.is_test_execution = False

  def run(self) -> dict[str, Any]:
    self._assert_not_test_dataset()
    documents = load_documents(
      self.root / self.config["corpus"]["raw_dir"],
      self.root / self.config["corpus"]["markdown_dir"],
    )
    samples = read_jsonl(self.root / self.config["dataset"]["path"])
    dataset_path = self.root / self.config["dataset"]["path"]
    dataset_sha256 = hashlib.sha256(dataset_path.read_bytes()).hexdigest()
    section_count = sum(
      1 for document in documents for block in document.blocks if block.heading_level is not None
    )
    LOGGER.info(
      "Documents=%d Sections=%d DatasetSamples=%d",
      len(documents), section_count, len(samples),
    )
    provider = self._provider()
    cached = CachedEmbeddingProvider(
      provider,
      self.root / self.config["embedding"]["cache_path"],
    )
    strategies: dict[str, Any] = {
      "fixed": FixedChunker(
        self.config["chunking"]["fixed"]["chunk_size"],
        self.config["chunking"]["fixed"]["overlap"],
      ),
      "structure": StructureAwareChunker(
        self.config["chunking"]["structure"]["max_tokens"],
        self.config["chunking"]["structure"]["heading_prefix"],
      ),
      "parent_child": ParentChildChunker(
        self.config["chunking"]["parent_child"]["child_max_tokens"],
        self.config["chunking"]["parent_child"]["heading_prefix"],
      ),
    }
    requested = self.config["chunking"].get("strategies", list(strategies))
    timestamp = datetime.now(UTC)
    experiment_id = f"{timestamp:%Y%m%dT%H%M%SZ}-{os.getpid()}"
    answerable_questions = [sample.question for sample in samples if sample.answerable]
    query_start = time.perf_counter()
    cached.embed_queries(answerable_questions)
    query_embedding_seconds = time.perf_counter() - query_start
    query_cache = {
      "embedding_seconds": query_embedding_seconds,
      "cache_hits": cached.hits,
      "cache_misses": cached.misses,
      "actual_embedding_count": cached.actual_embedding_count,
    }
    LOGGER.info(
      "SharedQueries=%d CacheHits=%d CacheMisses=%d ActualEmbeddings=%d Time=%.4fs",
      len(answerable_questions), cached.hits, cached.misses,
      cached.actual_embedding_count, query_embedding_seconds,
    )
    tokenizer_config = dict(self.config.get("tokenizer", {
      "provider": "approximate",
      "model": "rag-lab/lexical-approx-v1",
    }))
    if tokenizer_config.get("cache_dir"):
      tokenizer_config["cache_dir"] = str(self.root / tokenizer_config["cache_dir"])
    self.qwen_token_counter = build_token_counter(tokenizer_config)
    metadata = build_experiment_metadata(
      experiment_id=experiment_id,
      dataset_name=self.config["dataset"]["version"],
      dataset_path=dataset_path,
      corpus_manifest_path=self.root / self.config["corpus"].get(
        "manifest_path", "data/corpus/java-interview-real-v1/manifest.jsonl",
      ),
      embedding_model=cached.model_name,
      embedding_dimensions=cached.dimensions,
      tokenizer_model=self.config.get("tokenizer", {}).get(
        "model", self.qwen_token_counter.model_name,
      ),
      token_count_mode=self.qwen_token_counter.mode,
      device=self.config["embedding"].get("device") or "cpu/default",
      document_count=len(documents),
      query_count=len(answerable_questions),
      random_seed=self.config["experiment"].get("seed", 42),
      cloud_api_enabled=self.config.get("cloud", {}).get("enabled", False),
      project_root=self.root,
      timestamp=timestamp.isoformat(),
      test_executed=self.is_test_execution,
    )
    report: dict[str, Any] = {
      **metadata,
      "config": self.config,
      "dataset_version": self.config["dataset"]["version"],
      "dataset_sha256": dataset_sha256,
      "environment": {
        "python": sys.version,
        "os": platform.platform(),
        "device": self.config["embedding"].get("device") or "cpu/default",
      },
      "documents": len(documents),
      "dataset_samples": len(samples),
      "shared_query_embeddings": query_cache,
      "strategies": {},
    }
    for name in requested:
      report["strategies"][name] = self._run_strategy(
        name, strategies[name], documents, samples, cached,
      )
    cached.close()
    raw_path = self.root / "results/raw" / f"{experiment_id}.json"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    self._write_comparison(report)
    LOGGER.info("Experiment %s written to %s", experiment_id, raw_path)
    return report

  def _run_strategy(
    self,
    name: str,
    chunker: Any,
    documents: list[Any],
    samples: list[Any],
    provider: CachedEmbeddingProvider,
  ) -> dict[str, Any]:
    all_chunks = [chunk for document in documents for chunk in chunker.chunk(document)]
    chunks = [chunk for chunk in all_chunks if chunk.metadata.get("indexable", True)]
    parents = {chunk.id: chunk for chunk in all_chunks if not chunk.metadata.get("indexable", True)}
    prefix = name != "fixed" and self.config["chunking"][name].get("heading_prefix", False)
    texts = [embedding_text(chunk, prefix) for chunk in chunks]
    before_hits, before_misses = provider.hits, provider.misses
    before_actual = provider.actual_embedding_count
    embed_start = time.perf_counter()
    embeddings = provider.embed_documents(texts)
    embedding_seconds = time.perf_counter() - embed_start
    retriever = ExactDenseRetriever(chunks, embeddings, provider)
    retrieval_start = time.perf_counter()
    max_k = max(self.config["retrieval"]["top_k"])
    results: dict[str, list[Any]] = {}
    query_latencies: list[float] = []
    retrieval_calls = 0
    for sample in samples:
      if not sample.answerable:
        continue
      sample_start = time.perf_counter()
      # Hard-negative score margins require the highest-scoring mapped chunk,
      # not only Top-K. Other samples retain bounded Top-K retrieval.
      result_count = len(chunks) if sample.negative_evidences else max_k
      results[sample.id] = retriever.search(sample.question, result_count)
      query_latencies.append(time.perf_counter() - sample_start)
      retrieval_calls += 1
    retrieval_seconds = time.perf_counter() - retrieval_start
    evaluation_config = self.config["evaluation"]
    metrics = evaluate_results(
      samples,
      results,
      self.config["retrieval"]["top_k"],
      coverage_thresholds=evaluation_config.get(
        "evidence_coverage_thresholds", [0.25, 0.50, 0.75],
      ),
      primary_threshold=evaluation_config.get(
        "primary_coverage_threshold",
        evaluation_config.get("evidence_coverage_threshold", 0.50),
      ),
      any_overlap_threshold=evaluation_config.get("any_overlap_threshold", 0.01),
      parents=parents if parents else None,
    )
    token_summary = summarize_chunk_tokens(
      chunks,
      self.approximate_token_counter,
      self.qwen_token_counter,
    )
    output = {
      "chunk_count": len(chunks),
      "parent_count": len(parents),
      **token_summary,
      "index_size_estimate_bytes": len(chunks) * provider.dimensions * 4,
      "embedding_seconds": embedding_seconds,
      "retrieval_seconds": retrieval_seconds,
      "retrieval_calls": retrieval_calls,
      "p50_retrieval_latency_ms": self._percentile(query_latencies, 0.50) * 1000,
      "p95_retrieval_latency_ms": self._percentile(query_latencies, 0.95) * 1000,
      "average_candidates": statistics.fmean(
        len(result) for result in results.values()
      ) if results else 0,
      "embedding_cache_hits": provider.hits - before_hits,
      "embedding_cache_misses": provider.misses - before_misses,
      "actual_embedding_count": provider.actual_embedding_count - before_actual,
      "metrics": metrics,
    }
    LOGGER.info(
      "%s Documents=%d Chunks=%d CacheHits=%d CacheMisses=%d ActualEmbeddings=%d "
      "EmbeddingTime=%.4fs RetrievalTime=%.4fs EvidenceRecall@5/50=%.4f MRR=%.4f",
      name, len(documents), len(chunks), output["embedding_cache_hits"],
      output["embedding_cache_misses"], output["actual_embedding_count"],
      embedding_seconds, retrieval_seconds,
      metrics["Overall"]["EvidenceRecall@5/50"], metrics["Overall"]["MRR"],
    )
    return output

  def _provider(self) -> Any:
    config = self.config["embedding"]
    if config["provider"] == "hashing":
      return HashingEmbeddingProvider(config["dimensions"])
    if config["provider"] == "sentence_transformers":
      return SentenceTransformerEmbeddingProvider(
        model_name=config["model"],
        dimensions=config["dimensions"],
        device=config.get("device"),
        batch_size=config["batch_size"],
        local_files_only=config.get("local_files_only", True),
        cache_folder=str(self.root / config["model_cache_path"])
        if config.get("model_cache_path") else None,
      )
    raise ValueError(f"Unknown embedding provider: {config['provider']}")

  def _write_comparison(self, report: dict[str, Any]) -> None:
    configured_path = self.config.get("results", {}).get(
      "comparison_csv",
      "results/reports/chunking-comparison.csv",
    )
    path = self.root / configured_path
    path.parent.mkdir(parents=True, exist_ok=True)
    top_ks = self.config["retrieval"]["top_k"]
    fields = [
      "experiment_id", "strategy", "embedding_model", "dataset_version", "chunk_count",
      "parent_count", "approx_average_chunk_tokens", "qwen_average_chunk_tokens",
      "approx_p95_chunk_tokens", "qwen_p95_chunk_tokens", "token_count_mode",
      "index_size_estimate_bytes", "embedding_seconds", "retrieval_seconds",
      "retrieval_calls", "p50_retrieval_latency_ms", "p95_retrieval_latency_ms",
      "embedding_cache_hits", "embedding_cache_misses", "MRR",
      *[f"AnyOverlapRecall@{k}" for k in top_ks],
      *[f"EvidenceRecall@{k}/{threshold}" for k in top_ks
        for threshold in (25, 50, 75)],
      *[f"EvidenceCoverage@{k}" for k in top_ks],
      *[f"MicroEvidenceCoverage@{k}" for k in top_ks],
      *[f"AllEvidenceHit@{k}/50" for k in top_ks],
      *[f"ContextPrecision@{k}" for k in top_ks],
      *[f"ContextWaste@{k}" for k in top_ks],
      *[f"NegativeExposure@{k}Query" for k in top_ks],
      *[f"NegativeExposure@{k}Evidence" for k in top_ks],
      *[f"GoldBeforeNegative@{k}" for k in top_ks],
      "AverageGoldNegativeScoreMargin", "P50GoldNegativeScoreMargin",
      "MinimumGoldNegativeScoreMargin", "PairwiseGoldWinRate",
    ]
    rows = []
    for strategy, result in report["strategies"].items():
      overall = result["metrics"]["Overall"]
      rows.append({
        "experiment_id": report["experiment_id"],
        "strategy": strategy,
        "embedding_model": report["embedding_model"],
        "dataset_version": report["dataset_version"],
        **{field: result[field] for field in fields if field in result},
        **{field: overall[field] for field in fields if field in overall},
      })
    with path.open("w", encoding="utf-8", newline="") as handle:
      writer = csv.DictWriter(handle, fieldnames=fields)
      writer.writeheader()
      writer.writerows(rows)

  @staticmethod
  def _percentile(values: list[int] | list[float], quantile: float) -> float:
    if not values:
      return 0
    ordered = sorted(values)
    return float(ordered[round((len(ordered) - 1) * quantile)])

  def _git_commit(self) -> str:
    try:
      return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=self.root,
        text=True,
        stderr=subprocess.DEVNULL,
      ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
      return "NOT_AVAILABLE"

  def _assert_not_test_dataset(self) -> None:
    dataset = self.config.get("dataset", {})
    path_name = Path(str(dataset.get("path", ""))).name.lower()
    version = str(dataset.get("version", "")).lower()
    is_test = path_name.startswith("test") or "-test" in version or "_test" in version
    if not is_test:
      self.is_test_execution = False
      return
    execution = self.config.get("test_execution", {})
    if not execution.get("allow_agent_frozen_test_once", False):
      raise ValueError(
        "Phase 1.5 policy: Test is agent-reviewed, not human-frozen, and must be NOT EXECUTED",
      )
    freeze_path = self.root / execution["freeze_metadata_path"]
    ledger_path = self.root / execution["execution_ledger_path"]
    if ledger_path.exists():
      raise ValueError(f"Agent-frozen Test has already been executed: {ledger_path}")
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    dataset_path = self.root / dataset["path"]
    dataset_sha = hashlib.sha256(dataset_path.read_bytes()).hexdigest()
    dataset_count = sum(
      bool(line.strip())
      for line in dataset_path.read_text(encoding="utf-8").splitlines()
    )
    if (
      not freeze.get("frozen")
      or freeze.get("freeze_kind") != "AGENT_REVIEWED_NOT_HUMAN"
      or freeze.get("human_reviewed") is not False
      or freeze.get("count") != 40
      or dataset_count != 40
      or freeze.get("sha256") != dataset_sha
    ):
      raise ValueError("Agent-frozen Test metadata does not match the configured dataset")
    self.is_test_execution = True
