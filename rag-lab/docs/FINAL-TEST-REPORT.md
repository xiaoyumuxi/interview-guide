# Agent-Frozen Test Final Report

## Status

The 40-sample Test split was independently reviewed by
`final_test_freeze_reviewer`: 40 APPROVE, 0 REJECT. All 53 gold/negative Evidence
spans passed exact source-offset replay, provenance, source-file SHA-256, and
repository commit checks. The three unanswerable questions were also checked
against the fixed corpus.

This is an **agent review, not a human review**:

- freeze kind: `AGENT_REVIEWED_NOT_HUMAN`
- `human_reviewed=false`
- frozen Test SHA-256:
  `713b8b9dac822f067d2fd04f7c322014d5d4bb9adae546b712c6bc734b8d3475`
- final decisions SHA-256:
  `0497c680ace885b1b82bb6cd84f67c0b7c752aa383b56c2318e0c2887a35baf5`

After all Dev decisions were complete, the frozen Test was executed exactly
once. The execution ledger now refuses a second run.

- experiment: `20260728T115625Z-57404`
- embedding: local `Qwen/Qwen3-Embedding-0.6B`, 1024 dimensions
- retriever: exact cosine
- device: CPU for this Test run
- documents: 48
- Test samples: 40
- retrieval-metric queries: 37 answerable samples
- unanswerable samples: 3, retained in the dataset but excluded from ordinary
  recall because the retriever has no calibrated abstention mechanism

## Test results

| Strategy | Chunks | EvidenceRecall@5/50 | EvidenceCoverage@5 | AllEvidenceHit@5/50 | ContextPrecision@5 | MRR |
|---|---:|---:|---:|---:|---:|---:|
| Fixed | 889 | **0.9459** | 0.9220 | **0.9459** | 0.1200 | 0.7601 |
| Structure-Aware | 1,328 | **0.9459** | **0.9457** | **0.9459** | **0.1882** | **0.9052** |
| Parent-Child | 5,475 | 0.6892 | 0.6128 | 0.6757 | 0.5643 | 0.1270 |

Strict Recall@5/50 does not distinguish Fixed from Structure-Aware on Test.
Structure-Aware nevertheless recovers more of each Evidence span, returns cleaner
contexts, and ranks the first sufficiently covered Evidence earlier. It also has
better Top-1 strict recall (0.8108 vs 0.5946), while Fixed is slightly better at
Recall@3/50 (0.9459 vs 0.9189).

## Hard-negative result

There are five hard-negative Test queries.

| Strategy | NegativeExposure@5 Query | Avg gold-negative margin | Min margin | Pairwise gold win | Gold before negative@5 |
|---|---:|---:|---:|---:|---:|
| Fixed | 0.60 | 0.0933 | -0.0492 | 9/10 = 0.90 | 4/5 = 0.80 |
| Structure-Aware | **0.20** | **0.2604** | **0.1448** | **10/10 = 1.00** | **5/5 = 1.00** |
| Parent-Child | 0.00 | 0.2777 | 0.2777 | 1/1 = 1.00 | 1/5 = 0.20 |

Parent-Child's zero negative exposure is not a win: only one of five queries had
a mapped gold side, so its pairwise denominator is 1 rather than 10.

## Decision

Use Structure-Aware as the preferred offline candidate and keep Fixed as the
smaller control/fallback. Structure costs 49.4% more chunks than Fixed, but its
Test coverage, context precision, MRR, and hard-negative separation are
materially better at equal Recall@5/50. Reject the current Parent-Child
configuration.

Do not ship the Phase 1.5 rule-based Multi-Query + RRF path: it failed its Dev
gate and was intentionally not retuned against Test.

## Interpretation limits

- The split audit shows Test is concentrated in network, Redis, JVM, and MySQL,
  so it is best described as a domain-shift held-out set rather than an IID set.
- Review is independent-agent review, not human review.
- The one Test run used CPU while earlier Dev quality runs used MPS. Embeddings
  come from the same local Qwen model and exact retrieval path; do not use this
  run for cross-device latency claims.
- These are offline retrieval results, not online product quality or production
  A/B results.

## Artifacts

- review decisions:
  `data/datasets/java-interview-real-v1/agent-freeze-review/test-final-freeze-decisions.jsonl`
- review report:
  `data/datasets/java-interview-real-v1/agent-freeze-review/test-final-freeze-report.md`
- frozen Test:
  `data/datasets/java-interview-real-v1/test-agent-frozen.jsonl`
- freeze metadata:
  `data/datasets/java-interview-real-v1/AGENT-FROZEN-TEST.json`
- execution ledger:
  `results/test/AGENT-FROZEN-TEST-EXECUTION.json`
- raw result:
  `results/raw/20260728T115625Z-57404.json`
- comparison CSV:
  `results/reports/agent-frozen-test-final.csv`
