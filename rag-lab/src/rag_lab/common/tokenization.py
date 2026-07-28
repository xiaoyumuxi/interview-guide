from __future__ import annotations

import logging
import statistics
from typing import Any, Protocol

from rag_lab.common.text import LexicalApproxTokenizer
from rag_lab.models import DocumentChunk

LOGGER = logging.getLogger(__name__)


class TokenCounter(Protocol):
  model_name: str
  mode: str

  def count(self, text: str) -> int: ...


class LexicalApproxTokenCounter:
  model_name = "rag-lab/lexical-approx-v1"
  mode = "approximate"

  def __init__(self) -> None:
    self.tokenizer = LexicalApproxTokenizer()

  def count(self, text: str) -> int:
    return self.tokenizer.count(text)


class HuggingFaceTokenCounter:
  mode = "huggingface"

  def __init__(
    self,
    model_name: str,
    *,
    local_files_only: bool = True,
    trust_remote_code: bool = True,
    cache_dir: str | None = None,
    tokenizer: Any | None = None,
  ) -> None:
    self.model_name = model_name
    if tokenizer is None:
      from transformers import AutoTokenizer

      tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        local_files_only=local_files_only,
        trust_remote_code=trust_remote_code,
        cache_dir=cache_dir,
      )
    self.tokenizer = tokenizer

  def count(self, text: str) -> int:
    return len(self.tokenizer.encode(text, add_special_tokens=False))


def build_token_counter(config: dict[str, Any]) -> TokenCounter:
  provider = config.get("provider", "huggingface")
  if provider == "approximate":
    return LexicalApproxTokenCounter()
  if provider != "huggingface":
    raise ValueError(f"Unknown tokenizer provider: {provider}")
  try:
    return HuggingFaceTokenCounter(
      config["model"],
      local_files_only=config.get("local_files_only", True),
      trust_remote_code=True,
      cache_dir=config.get("cache_dir"),
    )
  except (OSError, RuntimeError, ImportError, ValueError) as exc:
    if not config.get("fallback_to_approximate", True):
      raise
    LOGGER.warning("TOKENIZER_FALLBACK_TO_APPROXIMATE: %s", exc)
    return LexicalApproxTokenCounter()


def summarize_chunk_tokens(
  chunks: list[DocumentChunk],
  approximate: TokenCounter,
  qwen: TokenCounter,
) -> dict[str, float | str]:
  # Counting is read-only: chunk IDs, source spans, and boundaries are never
  # passed back to a chunker or mutated.
  approximate_counts = [approximate.count(chunk.source_text or chunk.text) for chunk in chunks]
  qwen_counts = [qwen.count(chunk.source_text or chunk.text) for chunk in chunks]
  return {
    "approx_average_chunk_tokens": statistics.fmean(approximate_counts)
    if approximate_counts else 0.0,
    "qwen_average_chunk_tokens": statistics.fmean(qwen_counts) if qwen_counts else 0.0,
    "approx_p95_chunk_tokens": _percentile(approximate_counts, 0.95),
    "qwen_p95_chunk_tokens": _percentile(qwen_counts, 0.95),
    "tokenizer_model": qwen.model_name,
    "token_count_mode": qwen.mode,
  }


def _percentile(values: list[int], quantile: float) -> float:
  if not values:
    return 0.0
  ordered = sorted(values)
  return float(ordered[round((len(ordered) - 1) * quantile)])
