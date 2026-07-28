from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from rag_lab.embedding.providers import EmbeddingProvider
from rag_lab.models import DocumentChunk


@dataclass(frozen=True)
class SearchResult:
  chunk: DocumentChunk
  score: float
  rank: int
  source_query: str | None = None
  source_rank: int | None = None
  rrf_score: float | None = None
  dense_score: float | None = None
  sources: tuple[tuple[str, int, float], ...] = ()


class ExactDenseRetriever:
  def __init__(
    self,
    chunks: list[DocumentChunk],
    embeddings: np.ndarray,
    provider: EmbeddingProvider,
  ) -> None:
    if len(chunks) != len(embeddings):
      raise ValueError("Chunk and embedding counts differ")
    self.chunks = chunks
    self.embeddings = self._normalize(embeddings)
    self.provider = provider

  def search(self, query: str, top_k: int) -> list[SearchResult]:
    query_vector = self._normalize(self.provider.embed_queries([query]))[0]
    scores = query_vector @ self.embeddings.T
    order = np.argsort(-scores, kind="stable")[:top_k]
    return [
      SearchResult(
        self.chunks[index],
        float(scores[index]),
        rank,
        source_query=query,
        source_rank=rank,
        dense_score=float(scores[index]),
        sources=((query, rank, float(scores[index])),),
      )
      for rank, index in enumerate(order, start=1)
    ]

  @staticmethod
  def _normalize(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    return matrix / np.maximum(norms, 1e-12)
