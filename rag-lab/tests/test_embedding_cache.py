from pathlib import Path

import numpy as np

from rag_lab.embedding import CachedEmbeddingProvider, HashingEmbeddingProvider


def test_embedding_cache_hits_same_model_dimension_and_text(tmp_path: Path) -> None:
  provider = HashingEmbeddingProvider(dimensions=32)
  cache = CachedEmbeddingProvider(provider, tmp_path / "embeddings.sqlite3")
  first = cache.embed_documents(["相同文本", "另一个文本"])
  assert cache.misses == 2
  assert cache.actual_embedding_count == 2
  second = cache.embed_documents(["相同文本"])
  assert cache.hits == 1
  assert cache.actual_embedding_count == 2
  np.testing.assert_array_equal(first[0], second[0])
  cache.close()

