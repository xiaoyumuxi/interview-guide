from __future__ import annotations

import sqlite3
from pathlib import Path

import numpy as np

from rag_lab.common.text import text_hash
from rag_lab.embedding.providers import EmbeddingProvider


class CachedEmbeddingProvider:
  def __init__(self, provider: EmbeddingProvider, cache_path: Path) -> None:
    self.provider = provider
    self.model_name = provider.model_name
    self.dimensions = provider.dimensions
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    self._connection = sqlite3.connect(cache_path)
    self._connection.execute(
      """
      CREATE TABLE IF NOT EXISTS embeddings (
        model_name TEXT NOT NULL,
        dimensions INTEGER NOT NULL,
        kind TEXT NOT NULL,
        text_hash TEXT NOT NULL,
        vector BLOB NOT NULL,
        PRIMARY KEY (model_name, dimensions, kind, text_hash)
      )
      """
    )
    self.hits = 0
    self.misses = 0
    self.actual_embedding_count = 0

  def embed_documents(self, texts: list[str]) -> np.ndarray:
    return self._embed(texts, "document", self.provider.embed_documents)

  def embed_queries(self, queries: list[str]) -> np.ndarray:
    return self._embed(queries, "query", self.provider.embed_queries)

  def _embed(self, texts: list[str], kind: str, embedder: object) -> np.ndarray:
    if not texts:
      return np.empty((0, self.dimensions), dtype=np.float32)
    vectors: list[np.ndarray | None] = [None] * len(texts)
    missing: dict[str, list[int]] = {}
    for index, text in enumerate(texts):
      digest = text_hash(text)
      row = self._connection.execute(
        "SELECT vector FROM embeddings "
        "WHERE model_name = ? AND dimensions = ? AND kind = ? AND text_hash = ?",
        (self.model_name, self.dimensions, kind, digest),
      ).fetchone()
      if row:
        vectors[index] = np.frombuffer(row[0], dtype=np.float32).copy()
        self.hits += 1
      else:
        missing.setdefault(digest, []).append(index)
        self.misses += 1
    if missing:
      unique_texts = [texts[indexes[0]] for indexes in missing.values()]
      generated = embedder(unique_texts)  # type: ignore[operator]
      self.actual_embedding_count += len(unique_texts)
      for (digest, indexes), vector in zip(missing.items(), generated, strict=True):
        if vector.shape != (self.dimensions,):
          raise ValueError(f"Embedding shape {vector.shape} != ({self.dimensions},)")
        self._connection.execute(
          "INSERT OR REPLACE INTO embeddings VALUES (?, ?, ?, ?, ?)",
          (self.model_name, self.dimensions, kind, digest, vector.astype(np.float32).tobytes()),
        )
        for index in indexes:
          vectors[index] = vector
      self._connection.commit()
    return np.stack([vector for vector in vectors if vector is not None])

  def close(self) -> None:
    self._connection.close()

