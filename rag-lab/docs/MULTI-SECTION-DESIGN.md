# Multi-Section Retrieval Design

## Gold-blind decision boundary

The optimization receives only the question string. It cannot access
`QuerySample.type`, gold evidence, negative evidence, or the reference answer.
`MultiSectionQueryDetector` uses deterministic surface signals. The decomposer
returns no subqueries when a split is not reliable, even if the detector found a
weak conjunction.

## Query decomposition

`RuleBasedChineseQueryDecomposer` handles explicit comparison, “分别/各自”
enumeration, three-item Chinese lists, and “为什么 A 而 B” forms. It preserves
English identifiers, method names, and class names, emits at most four
subqueries, and never calls a model. The original query remains an independent
retrieval route.

## Retrieval and fusion

Each original/subquery route embeds through the existing
`CachedEmbeddingProvider` and performs Exact Cosine Search with Top-20
candidates. Scores from different routes are not directly compared. Reciprocal
Rank Fusion uses:

```text
RRF(d) = sum(1 / (60 + rank_i(d)))
```

Each fused result keeps all contributing source queries, source ranks, dense
scores, and its final RRF score for debugging.

## Section diversity

The diversity reranker caps final results from the same
`(document_id, heading_path)` at two. It changes only final candidate ordering
and never sees gold. Candidate retrieval remains unchanged.

## Context assembly

Ranking and context are separate artifacts. `ContextAssembler` may add neighbor
chunks or a parent section, deduplicates overlapping source spans, enforces a
3,000-token budget, and limits repeated sections. Expansion affects only
assembled-context coverage, precision, waste, and token counts; it cannot change
retrieval metrics.

## Ablation

- S0: original query + Structure-Aware Exact Search
- S1: original + subqueries + RRF
- S2: S1 + section diversity
- S3: S2 ranking + context expansion

S3 must reuse the byte-identical S2 ranking. Current Dev and Hard Dev are
reported separately. Test is `NOT EXECUTED`.
