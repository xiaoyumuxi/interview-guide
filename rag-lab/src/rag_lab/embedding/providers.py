from __future__ import annotations

import hashlib
import re
from typing import Protocol

import numpy as np

from rag_lab.common.text import normalize_for_hash


class EmbeddingProvider(Protocol):
  model_name: str
  dimensions: int

  def embed_documents(self, texts: list[str]) -> np.ndarray: ...

  def embed_queries(self, queries: list[str]) -> np.ndarray: ...


def _l2_normalize(matrix: np.ndarray) -> np.ndarray:
  norms = np.linalg.norm(matrix, axis=1, keepdims=True)
  return matrix / np.maximum(norms, 1e-12)


class HashingEmbeddingProvider:
  """Dependency-light local baseline. It is deterministic, not a neural-model substitute."""

  model_name = "rag-lab/hashing-char-word-v1"

  def __init__(self, dimensions: int = 1024) -> None:
    self.dimensions = dimensions

  def embed_documents(self, texts: list[str]) -> np.ndarray:
    return self._embed(texts)

  def embed_queries(self, queries: list[str]) -> np.ndarray:
    return self._embed(queries)

  def _embed(self, texts: list[str]) -> np.ndarray:
    matrix = np.zeros((len(texts), self.dimensions), dtype=np.float32)
    for row, raw in enumerate(texts):
      text = normalize_for_hash(raw).casefold()
      features = re.findall(r"[a-z0-9_.+#-]+", text)
      compact = re.sub(r"\s+", "", text)
      features.extend(compact[index:index + size]
                      for size in (1, 2, 3)
                      for index in range(max(0, len(compact) - size + 1)))
      for feature in features:
        digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
        value = int.from_bytes(digest)
        column = value % self.dimensions
        sign = 1.0 if value & 1 else -1.0
        matrix[row, column] += sign
    return _l2_normalize(matrix)


class SentenceTransformerEmbeddingProvider:
  """Local sentence-transformers adapter; no API calls are made."""

  def __init__(
    self,
    model_name: str = "Qwen/Qwen3-Embedding-0.6B",
    dimensions: int = 1024,
    device: str | None = None,
    batch_size: int = 32,
    local_files_only: bool = True,
    cache_folder: str | None = None,
  ) -> None:
    try:
      from sentence_transformers import SentenceTransformer
    except ImportError as exc:
      raise RuntimeError("Install the 'qwen' optional dependency for neural embeddings") from exc
    self.model_name = model_name
    self.dimensions = dimensions
    self.batch_size = batch_size
    self._model = SentenceTransformer(
      model_name,
      device=device,
      local_files_only=local_files_only,
      truncate_dim=dimensions,
      cache_folder=cache_folder,
    )

  def embed_documents(self, texts: list[str]) -> np.ndarray:
    return self._encode(texts, prompt_name=None)

  def embed_queries(self, queries: list[str]) -> np.ndarray:
    return self._encode(queries, prompt_name="query")

  def _encode(self, texts: list[str], prompt_name: str | None) -> np.ndarray:
    return np.asarray(self._model.encode(
      texts,
      batch_size=self.batch_size,
      normalize_embeddings=True,
      show_progress_bar=False,
      prompt_name=prompt_name,
    ), dtype=np.float32)
