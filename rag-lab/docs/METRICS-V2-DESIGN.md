# Metric V2 Design

## Scope and evaluation boundary

Metric V2 evaluates retrieval against immutable source spans from the
`java-interview-real-v1` Markdown corpus. Retrieval may embed a heading path plus
the chunk body, but evaluation never counts injected headings, synthetic table
headers, or any other text outside the chunk's source offsets.

The benchmark keeps two layers separate:

- **Retrieval metrics** use only the final ranked Top-K chunks.
- **Context metrics** use only the spans emitted by `ContextAssembler`.

Expansion in the context layer therefore cannot be reported as a retrieval gain.
The current 40-sample Test candidate remains `NOT EXECUTED`; all Phase 1.5
experiments use Current Dev or Hard Dev.

## Span model

Every evidence and chunk is represented by:

```text
(document_id, start_offset, end_offset)
```

Offsets are half-open. Intervals are merged independently per document, and both
overlapping and adjacent intervals are coalesced. This prevents fixed-window
overlap or repeated multi-query results from counting the same source characters
more than once.

`DocumentChunk` exposes:

- `embedding_text`: text sent to the embedding provider;
- `source_text`: original source content represented by the offsets;
- `start_offset` / `end_offset`: the authoritative evaluation span.

The legacy `text` attribute is retained as a compatibility alias for existing
chunker tests and callers.

## Retrieval metrics

For evidence span \(e\), let \(U_K(d)\) be the union of Top-K retrieved spans in
document \(d\). Evidence coverage is:

```text
coverage(e, K) = |e ∩ U_K(e.document_id)| / |e|
```

- `EvidenceCoverage@K`: macro average of per-evidence coverage, then query
  average.
- `MicroEvidenceCoverage@K`: covered gold characters divided by all gold
  characters, aggregated across queries.
- `EvidenceRecall@K/T`: fraction of gold evidence whose coverage is at least
  threshold `T`; thresholds are 25%, 50%, and 75%.
- `AllEvidenceHit@K/50`: query indicator that every gold evidence reaches 50%
  coverage. This is the primary completeness measure for Multi-Section queries.
- `AnyOverlapRecall@K`: compatibility metric using 1% evidence coverage. It is
  never abbreviated to `Recall@K`.
- `MRR`: reciprocal rank of the first chunk that covers at least 50% of any gold
  evidence. For Multi-Section it is auxiliary because it says nothing about the
  remaining evidence.

## Context metrics

For assembled context span union \(C_K\) and gold span union \(G\):

```text
ContextPrecision@K = |C_K ∩ G| / |C_K|
ContextWaste@K     = 1 - ContextPrecision@K
```

Both numerator and denominator use merged original source spans. Heading
prefixes are absent from the denominator. Context coverage reuses the evidence
coverage definition against the assembled spans. `ApproxContextTokens` records
the lexical budget used by the unchanged Phase 1 assembler; audit reports also
recount the same context with the Qwen tokenizer under a separate `qwen_` field.

## Hard-negative metrics

Gold and negative evidence are mapped to chunks by source-span coverage. If an
evidence maps to multiple chunks, its evidence score is the highest dense score
among covering chunks.

- `NegativeExposure@KQuery`: fraction of hard-negative queries with at least one
  negative evidence covered by a Top-K chunk.
- `NegativeExposure@KEvidence`: fraction of negative evidence covered in Top-K.
- `Average/P50/MinimumGoldNegativeScoreMargin`: distribution of
  `best_gold_score - best_negative_score` per hard-negative query.
- `PairwiseGoldWinRate`: fraction of all gold-negative evidence score pairs where
  the gold score is strictly larger.
- `GoldBeforeNegative@K`: success when the first gold rank is before the first
  negative rank; an absent negative is a gold win, while an absent gold is a
  failure.

All coverage-based mappings use the configured primary threshold (50%) unless a
metric name explicitly states another threshold.

## Aggregation and reporting

Each query first produces sufficient statistics (covered and total characters,
evidence hits, ranks, and negative pairs). Group aggregation preserves ratios:
macro values average query values, while micro coverage sums characters before
division. Reports retain Overall and query-type groups, and additionally expose
Hard Dev difficulty groups when present.

The main comparison column is `EvidenceRecall@5/50`. The report must present it
with `EvidenceCoverage@5`, `AllEvidenceHit@5/50`, `ContextPrecision@5`, MRR,
index cost, and latency; no single metric decides migration.
