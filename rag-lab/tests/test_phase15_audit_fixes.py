from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

from rag_lab.common.experiment import REQUIRED_EXPERIMENT_METADATA, build_experiment_metadata
from rag_lab.common.tokenization import (
  HuggingFaceTokenCounter,
  LexicalApproxTokenCounter,
  build_token_counter,
  summarize_chunk_tokens,
)
from rag_lab.dataset.models import Evidence, QuerySample, QueryType
from rag_lab.evaluation.exports import build_hard_negative_rows, write_hard_negative_csv
from rag_lab.evaluation.metrics import evaluate_results
from rag_lab.models import DocumentChunk
from rag_lab.retrieval import SearchResult
from rag_lab.retrieval.performance import preload_query_cache


def _evidence(evidence_id: str, start: int, end: int) -> Evidence:
  return Evidence(
    id=evidence_id,
    document_id="doc",
    heading_path=["H"],
    start_offset=start,
    end_offset=end,
    text="字" * (end - start),
  )


def _negative_sample(sample_id: str, query_type: QueryType) -> QuerySample:
  return QuerySample(
    id=sample_id,
    question=f"{sample_id} 的问题",
    reference_answer="答案",
    evidences=[_evidence(f"{sample_id}-gold", 0, 4)],
    negative_evidences=[_evidence(f"{sample_id}-negative", 6, 10)],
    negative_evidence_ids=[f"{sample_id}-negative"],
    type=query_type,
  )


def _ranked() -> list[SearchResult]:
  return [
    SearchResult(DocumentChunk("gold", "doc", "字" * 4, 0, 4, ["H"]), 0.8, 1),
    SearchResult(DocumentChunk("negative", "doc", "字" * 4, 6, 10, ["H"]), 0.6, 2),
  ]


def test_hard_negative_csv_identity_fields(tmp_path: Path) -> None:
  report = {
    "experiment_id": "exp-1",
    "strategies": {
      "fixed": {
        "metrics": {
          "HARD_NEGATIVE": {"HardNegativeQueryCount": 1},
          "NEGATIVE_BEARING": {"NegativeBearingQueryCount": 2},
        },
      },
    },
  }
  rows = build_hard_negative_rows({"current_dev": report})
  output = tmp_path / "hard-negative.csv"
  write_hard_negative_csv(rows, output)
  csv_rows = list(csv.DictReader(output.open()))
  assert csv_rows
  assert all(row["experiment_id"] and row["dataset"] and row["strategy"] for row in csv_rows)


def test_negative_bearing_group() -> None:
  hard = _negative_sample("hard", QueryType.HARD_NEGATIVE)
  paraphrase = _negative_sample("para", QueryType.PARAPHRASE)
  metrics = evaluate_results(
    [hard, paraphrase],
    {"hard": _ranked(), "para": _ranked()},
    [1, 2],
  )
  assert metrics["HARD_NEGATIVE"]["HardNegativeQueryCount"] == 1
  assert metrics["NEGATIVE_BEARING"]["NegativeBearingQueryCount"] == 2


def test_hard_negative_effective_counts() -> None:
  mapped = _negative_sample("mapped", QueryType.HARD_NEGATIVE)
  unmapped = _negative_sample("unmapped", QueryType.HARD_NEGATIVE)
  metrics = evaluate_results(
    [mapped, unmapped],
    {
      "mapped": _ranked(),
      "unmapped": [
        SearchResult(DocumentChunk("other", "other", "x", 0, 1, []), 0.9, 1),
      ],
    },
    [1, 2],
  )["HARD_NEGATIVE"]
  assert metrics["HardNegativeQueryCount"] == 2
  assert metrics["NegativeBearingQueryCount"] == 2
  assert metrics["GoldMappedQueryCount"] == 1
  assert metrics["NegativeMappedQueryCount"] == 1
  assert metrics["MarginEligibleQueryCount"] == 1
  assert metrics["PairwiseComparisonCount"] == 1


def test_pairwise_rate_has_denominator() -> None:
  sample = _negative_sample("q", QueryType.HARD_NEGATIVE)
  metrics = evaluate_results([sample], {"q": _ranked()}, [1, 2])["NEGATIVE_BEARING"]
  assert metrics["PairwiseGoldWinRate"] == 1
  assert metrics["PairwiseGoldWinCount"] == 1
  assert metrics["PairwiseComparisonCount"] == 1
  assert metrics["GoldBeforeNegativeRate@2"] == 1
  assert metrics["GoldBeforeNegativeSuccessCount@2"] == 1
  assert metrics["GoldBeforeNegativeQueryCount@2"] == 1


class _FakeTokenizer:
  def encode(self, text: str, add_special_tokens: bool = False) -> list[int]:
    assert add_special_tokens is False
    return list(range(len(text.split())))


def test_token_counter_huggingface() -> None:
  counter = HuggingFaceTokenCounter("fake/qwen", tokenizer=_FakeTokenizer())
  assert counter.count("one two three") == 3
  assert counter.mode == "huggingface"


def test_token_counter_fallback(monkeypatch: object) -> None:
  def fail(*args: object, **kwargs: object) -> object:
    raise OSError("not local")

  monkeypatch.setattr(  # type: ignore[attr-defined]
    "rag_lab.common.tokenization.HuggingFaceTokenCounter", fail,
  )
  counter = build_token_counter({
    "provider": "huggingface",
    "model": "missing/model",
    "local_files_only": True,
    "fallback_to_approximate": True,
  })
  assert isinstance(counter, LexicalApproxTokenCounter)
  assert counter.mode == "approximate"


def test_existing_chunks_not_rechunked() -> None:
  chunks = [
    DocumentChunk("a", "doc", "第一段", 0, 3, ["H"]),
    DocumentChunk("b", "doc", "second block", 3, 15, ["H"]),
  ]
  boundaries = [(chunk.id, chunk.start_offset, chunk.end_offset) for chunk in chunks]
  summary = summarize_chunk_tokens(
    chunks,
    LexicalApproxTokenCounter(),
    HuggingFaceTokenCounter("fake/qwen", tokenizer=_FakeTokenizer()),
  )
  assert summary["approx_average_chunk_tokens"] > 0
  assert summary["qwen_average_chunk_tokens"] > 0
  assert boundaries == [(chunk.id, chunk.start_offset, chunk.end_offset) for chunk in chunks]


class _CacheProbe:
  def __init__(self) -> None:
    self.cached: set[str] = set()
    self.hits = 0
    self.misses = 0

  def embed_queries(self, queries: list[str]) -> np.ndarray:
    for query in queries:
      if query in self.cached:
        self.hits += 1
      else:
        self.cached.add(query)
        self.misses += 1
    return np.zeros((len(queries), 2), dtype=np.float32)


def test_warm_ablation_uses_preloaded_query_cache() -> None:
  provider = _CacheProbe()
  queries = ["原问题", "子问题一", "子问题二"]
  preload_query_cache(provider, queries)
  misses_after_preload = provider.misses
  provider.embed_queries(queries)
  assert provider.misses == misses_after_preload
  assert provider.hits == len(queries)


def test_experiment_metadata_complete(tmp_path: Path) -> None:
  dataset = tmp_path / "dev.jsonl"
  dataset.write_text(json.dumps({"id": "q"}) + "\n")
  manifest = tmp_path / "manifest.json"
  manifest.write_text("{}")
  metadata = build_experiment_metadata(
    experiment_id="exp",
    dataset_name="dev",
    dataset_path=dataset,
    corpus_manifest_path=manifest,
    embedding_model="Qwen/Qwen3-Embedding-0.6B",
    embedding_dimensions=1024,
    tokenizer_model="Qwen/Qwen3-Embedding-0.6B",
    token_count_mode="huggingface",
    device="cpu",
    document_count=48,
    query_count=80,
    random_seed=42,
    cloud_api_enabled=False,
    project_root=tmp_path,
  )
  assert REQUIRED_EXPERIMENT_METADATA <= metadata.keys()


def test_test_executed_is_false(tmp_path: Path) -> None:
  dataset = tmp_path / "dev.jsonl"
  dataset.write_text("")
  manifest = tmp_path / "manifest.json"
  manifest.write_text("{}")
  metadata = build_experiment_metadata(
    experiment_id="exp",
    dataset_name="dev",
    dataset_path=dataset,
    corpus_manifest_path=manifest,
    embedding_model="model",
    embedding_dimensions=1,
    tokenizer_model="tokenizer",
    token_count_mode="approximate",
    device="cpu",
    document_count=0,
    query_count=0,
    random_seed=42,
    cloud_api_enabled=False,
    project_root=tmp_path,
  )
  assert metadata["test_executed"] is False
