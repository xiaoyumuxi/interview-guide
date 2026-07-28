#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag_lab.common.pipeline import load_documents  # noqa: E402
from rag_lab.dataset import DatasetBuilder, DatasetValidator  # noqa: E402
from rag_lab.dataset.io import write_jsonl  # noqa: E402
from rag_lab.embedding import (  # noqa: E402
  HashingEmbeddingProvider,
  SentenceTransformerEmbeddingProvider,
)


def main() -> None:
  parser = argparse.ArgumentParser(description="Build an evidence-span-grounded offline dataset")
  parser.add_argument("--target", type=int, default=100)
  parser.add_argument("--seed", type=int, default=42)
  parser.add_argument("--raw-dir", type=Path, default=ROOT / "data/raw")
  parser.add_argument("--output-dir", type=Path, default=ROOT / "data/datasets")
  parser.add_argument("--duplicate-threshold", type=float, default=0.90)
  parser.add_argument(
    "--dedup-provider",
    choices=["hashing", "qwen"],
    default="hashing",
  )
  parser.add_argument("--model-cache-path", type=Path, default=ROOT / "data/cache/models")
  parser.add_argument("--device", default="cpu")
  args = parser.parse_args()
  documents = load_documents(args.raw_dir, ROOT / "data/markdown")
  builder = DatasetBuilder(seed=args.seed)
  evidences = builder.sample_evidence(documents)
  candidate_target = math.ceil(args.target * 1.4)
  candidates = builder.build(evidences, candidate_target)
  document_map = {document.document_id: document for document in documents}
  errors = [
    error
    for sample in candidates
    for error in DatasetValidator().validate([sample], document_map)
  ]
  if errors:
    raise SystemExit("dataset validation failed:\n" + "\n".join(errors))
  exact_deduplicated = []
  seen_questions: set[str] = set()
  for sample in candidates:
    normalized_question = " ".join(sample.question.split()).casefold()
    if normalized_question not in seen_questions:
      seen_questions.add(normalized_question)
      exact_deduplicated.append(sample)
  if args.dedup_provider == "qwen":
    dedup_provider = SentenceTransformerEmbeddingProvider(
      model_name="Qwen/Qwen3-Embedding-0.6B",
      dimensions=1024,
      device=args.device,
      batch_size=16,
      local_files_only=True,
      cache_folder=str(args.model_cache_path),
    )
  else:
    dedup_provider = HashingEmbeddingProvider()
  embeddings = dedup_provider.embed_queries([sample.question for sample in exact_deduplicated])
  semantic_duplicates = DatasetValidator.semantic_duplicates(
    exact_deduplicated, embeddings, args.duplicate_threshold,
  )
  duplicate_ids = {right for _, right, _ in semantic_duplicates}
  deduplicated = [
    sample for sample in exact_deduplicated if sample.id not in duplicate_ids
  ]
  samples = builder.select_balanced(deduplicated, args.target)
  final_errors = DatasetValidator().validate(samples, document_map)
  if final_errors:
    raise SystemExit("final dataset validation failed:\n" + "\n".join(final_errors))
  dev, test = builder.stratified_split(samples)
  write_jsonl(args.output_dir / "candidates.jsonl", candidates)
  write_jsonl(args.output_dir / "all.jsonl", samples)
  write_jsonl(args.output_dir / "dev.jsonl", dev)
  write_jsonl(args.output_dir / "test.jsonl", test)
  print(
    f"documents={len(documents)} evidences={len(evidences)} "
    f"candidates={len(candidates)} exact_unique={len(exact_deduplicated)} "
    f"samples={len(samples)}"
  )
  print(f"dev={len(dev)} test={len(test)} types={dict(Counter(s.type.value for s in samples))}")
  print(f"semantic_duplicate_candidates={len(semantic_duplicates)} threshold={args.duplicate_threshold}")
  print(f"dedup_provider={dedup_provider.model_name}")


if __name__ == "__main__":
  main()
