from __future__ import annotations

from typing import Protocol


class QueryEmbeddingCache(Protocol):
  def embed_queries(self, queries: list[str]) -> object: ...


def preload_query_cache(provider: QueryEmbeddingCache, queries: list[str]) -> None:
  provider.embed_queries(list(dict.fromkeys(queries)))
