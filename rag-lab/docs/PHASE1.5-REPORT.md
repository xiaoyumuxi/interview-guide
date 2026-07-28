# RAG Lab Phase 1.5 Report

## 1. Current problem

Phase 1 treated a gold evidence as retrieved when one chunk covered at least 1%
of it. That compatibility metric is now named `AnyOverlapRecall@K`. It can count
a few matching characters as success, cannot tell whether all sections of a
comparison were found, and says nothing about irrelevant source content in the
returned chunks.

Phase 1.5 keeps the same 48 documents, source commits, evidence spans, three
chunker semantics, local Qwen3-Embedding-0.6B, and exact cosine search. The
original Phase 1.5 analysis was Dev-only. After it was finalized, the user
authorized an independent agent review, agent freeze, and exactly one Test run;
see `FINAL-TEST-REPORT.md`.

## 2. Metric V2

All intervals are half-open source offsets and are unioned per document before
counting:

```text
EvidenceCoverage(e, K) = |e ∩ union(Top-K source spans)| / |e|
EvidenceRecall@K/T     = fraction of evidence with coverage >= T
AllEvidenceHit@K/T     = every evidence reaches T
ContextPrecision@K     = relevant retrieved source chars / retrieved source chars
ContextWaste@K         = 1 - ContextPrecision@K
```

The primary threshold is 50%; 25% and 75% are also reported. MRR uses the first
chunk reaching 50% coverage and is auxiliary for Multi-Section. Heading prefixes
and synthetic table headers remain valid embedding text but are excluded from
source-span metrics.

Hard-negative metrics map gold and negative evidence to covering chunks and
report NegativeExposure, gold-negative score margins, pairwise wins, and whether
gold ranks before negative.

Implementation and formulas are in `src/rag_lab/evaluation/spans.py`,
`src/rag_lab/evaluation/metrics.py`, and `docs/METRICS-V2-DESIGN.md`.

## 3. Old and new metric interpretation

- `AnyOverlapRecall`: compatibility signal; “some part appeared.”
- `EvidenceRecall`: thresholded evidence completeness.
- `EvidenceCoverage`: continuous fraction of the source evidence recovered.
- `ContextPrecision`: how much returned source content is actually gold.

On Current Dev, the gap between AnyOverlap@5 and strict Recall@5/50 is 2.74
points for Fixed, 0.91 for Structure, and **26.03** for Parent-Child. On Hard
Dev, the Parent-Child gap is **34.72** points. The old metric therefore
materially overstated the child retrieval strategy and hid incomplete evidence.

Threshold sensitivity on Current Dev:

| Strategy | Recall@5/25 | Recall@5/50 | Recall@5/75 |
|---|---:|---:|---:|
| Fixed | 0.9635 | 0.9361 | 0.9064 |
| Structure | 0.9703 | 0.9658 | 0.9543 |
| Parent-Child | 0.8562 | 0.6279 | 0.5091 |

## 4. Three chunkers under Metric V2

Current Dev, 80 agent-reviewed samples:

| Strategy | Chunks | AnyOverlap@5 | Recall@5/50 | Coverage@5 | AllHit@5/50 | ContextPrecision@5 | MRR |
|---|---:|---:|---:|---:|---:|---:|---:|
| Fixed | 889 | 0.9635 | 0.9361 | 0.9362 | 0.9041 | 0.1220 | 0.8293 |
| Structure | 1,328 | 0.9749 | **0.9658** | **0.9633** | **0.9315** | **0.2085** | **0.8852** |
| Parent-Child | 5,475 | 0.8881 | 0.6279 | 0.6526 | 0.5890 | 0.5047 | 0.2767 |

Structure is genuinely better than Fixed on Current Dev, not merely under 1%
overlap. It costs 49.4% more chunks and estimated vector storage (5.19 MiB vs
3.47 MiB). Parent-Child's high precision reflects very small child spans, but its
strict completeness and MRR are unacceptable; its index is about 21.39 MiB.

The Hard Query Dev Set reverses part of the conclusion:

| Strategy | Recall@5/50 | Coverage@5 | AllHit@5/50 | ContextPrecision@5 | MRR |
|---|---:|---:|---:|---:|---:|
| Fixed | **0.7812** | **0.7887** | **0.7083** | 0.1268 | **0.5873** |
| Structure | 0.7118 | 0.7019 | 0.6250 | **0.1909** | 0.5431 |
| Parent-Child | 0.2882 | 0.3138 | 0.2292 | 0.2710 | 0.1635 |

Structure retrieves cleaner context, but it is not universally more robust.
Migration should therefore keep Fixed as a fallback/control rather than replace
it unconditionally.

## 5. Hard-negative analysis

Current Dev hard-negative queries:

| Strategy | NegativeExposure@5 | Avg margin | Min margin | Pairwise win | Gold before negative@5 |
|---|---:|---:|---:|---:|---:|
| Fixed | 0.4444 | 0.0990 | 0.0000 | 0.9000 | 0.7778 |
| Structure | **0.2222** | 0.1504 | 0.0177 | **1.0000** | **1.0000** |
| Parent-Child | 0.0000 | 0.1741 | 0.1039 | 1.0000 | 0.4444 |

The Hard Query Dev Set exposes a Fixed failure: minimum margin is -0.0161 and pairwise win
rate is 0.90. Structure has lower NegativeExposure@5 (0.1333), positive minimum
margin (0.0184), and 0.95 pairwise win rate.

NegativeExposure cannot be interpreted alone. Parent-Child exposes no negatives
at Top-5 largely because it also fails to retrieve gold; its GoldBeforeNegative@5
is only 0.2667 on the Hard Query Dev Set.

The audit-fixed denominator view shows why: Current Dev has 9 HARD_NEGATIVE and
9 NEGATIVE_BEARING queries. Fixed/Structure map both sides for 9/9 queries, while
Parent-Child is margin-eligible for only 2/9. The Hard Query Dev Set has 15
HARD_NEGATIVE but 26 NEGATIVE_BEARING queries. On the full derived group,
Structure's pairwise rate is 34/39 = 0.8718; Fixed is 33/39 = 0.8462;
Parent-Child reports 5/5 = 1.0 but is margin-eligible for only 5/26 queries.
Rates are therefore always reported with their effective denominator.

## 6. Hard Query Dev Set

The Hard Query Dev Set contains 48 samples, exactly four in each of 12 categories.
It **reuses the Dev Evidence Pool**, but uses more implicit and complex question
wording to measure query difficulty and retrieval robustness. It does not measure
generalization to new documents or topics and is not an independent split.
It includes scenario diagnosis, implicit paraphrase,
constraint selection, code behavior, terminology disambiguation, real
multi-section reasoning, and implementation differences.

The review history is preserved:

- first pass: 36 approve, 12 reject;
- independent targeted re-review: 10 approve, 2 reject;
- final independent re-review: 2 approve.

Final status is `AGENT_REVIEWED_NOT_HUMAN`, never human-reviewed. Exact offset,
evidence hash, section, span-overlap, answer reuse, and near-question leakage
checks pass. During Phase 1.5 tuning, Test was read only for leakage checks and
never executed.

## 7. Multi-Section ablation

Structure-Aware results:

### Current Dev Multi-Section

| Scheme | Recall@5/50 | Coverage@5 | AllHit@5/50 | ContextPrecision@5 |
|---|---:|---:|---:|---:|
| S0 dense baseline | **0.7917** | **0.7926** | **0.5833** | **0.3833** |
| S1 multi-query + RRF | 0.6806 | 0.6815 | 0.3333 | 0.3499 |
| S2 + diversity | 0.6806 | 0.6815 | 0.3333 | 0.3483 |

### Hard Query Dev Multi-Section

| Scheme | Recall@5/50 | Coverage@5 | AllHit@5/50 | ContextPrecision@5 |
|---|---:|---:|---:|---:|
| S0 | 0.3889 | 0.3889 | 0.1667 | 0.1796 |
| S1 | 0.3889 | 0.3889 | 0.1667 | 0.1796 |
| S2 | 0.3889 | 0.3889 | 0.1667 | 0.1796 |

The proposed decomposition does **not** meet the success criteria. It hurts all
three Current Dev Multi-Section primary metrics and provides no Hard Query Dev
Multi-Section gain. RRF can promote repeated partial matches from decomposed
routes and displace a chunk selected by the stronger complete original query.
The two-chunk section cap has almost no effect because the fused Top-5 was not
primarily failing from same-section duplication.

Multi-Section MRR is not used to override this result: a high first relevant rank
does not show that all gold evidence was recovered.

## 8. Context quality and cost

S3 reuses S2 ranking byte-for-byte. On Current Dev Overall, expansion changes
coverage from 0.9339 to 0.9358 but precision from 0.2000 to **0.1178**, using
2,639 approximate lexical tokens / 2,212 Qwen tokens on average. On Hard Query
Dev Overall, coverage rises from 0.7123 to 0.8025, but precision falls from
0.1977 to **0.1141**, using 2,826 approximate / 2,341 Qwen tokens.

For Hard Query Dev Multi-Section, assembled coverage rises from 0.3889 to 0.4722 while
precision falls from 0.1796 to 0.1172. This is a real context coverage gain but
an unacceptable default noise/cost tradeoff.

The original table mixed S1 cold-cache latency with S2 warm-cache latency and is
superseded by the audit-fixed measurements below. All horizontal comparisons use
the same warm cache and CPU device; quality metrics remain the original MPS run.

| Scheme | Queries | Subqueries | Warm cache hit/miss | Warm P50 ms | Warm P95 ms |
|---|---:|---:|---:|---:|---:|
| S0 | 73 | 0 | 73 / 0 | 0.115 | 0.122 |
| S1 | 73 | 44 | 117 / 0 | 0.132 | 0.663 |
| S2 | 73 | 44 | 117 / 0 | 0.127 | 0.679 |
| S3 | 73 | 44 | 117 / 0 | 1.227 | 1.627 |

Cold-cache P95 is 376.5 ms for S0, 1020.9 ms for S1, 1054.4 ms for S2,
and 1117.3 ms for S3 on Current Dev. The Hard Query Dev Set uses 48 queries,
29 generated subqueries, and 77 query embeddings.
Multi-query increases embedding and retrieval calls by about 60% without meeting
the quality gate. The cold P95 includes local Qwen embedding misses; warm-cache
figures are reported separately rather than hidden.

## 9. Failure cases

The reproducible cases are in `results/reports/failure-case-analysis.csv`.

- Fixed succeeds, Structure fails: `java_real_candidate_151`, where Fixed covers
  all poll/select evidence but Structure covers two of three sections.
- Structure succeeds, Fixed fails: `java_real_candidate_143`, the
  optimistic/pessimistic lock comparison (Structure 1.0 vs Fixed 0.5 coverage).
- Multi-query improves: `hard_dev_041`, RocketMQ instance/topic/queue boundaries
  (0.0 to 1.0 coverage).
- Multi-query degrades: `java_real_candidate_131`, synchronized vs
  ReentrantLock (1.0 to 0.5).
- Hard-negative ordering failure: `hard_dev_007`, where the Structure Top-10
  does not put a 50%-covered gold chunk before the negative.

There are 7 Fixed-success/Structure-fail cases, 5 inverse cases, 1 clear
multi-query improvement, 5 clear degradations, and 4 hard-negative ordering
failures under the diagnostic thresholds.

## 10. Recommendation

1. **Migrate Metric V2 and Test-execution guard.** These are clear reliability
   improvements.
2. **Pilot Structure-Aware, do not make it the sole production strategy.** It
   wins Current Dev and context precision but loses strict recall on the Hard Query Dev Set.
3. **Do not ship the current rule decomposition + RRF.** It fails the declared
   Multi-Section gate and costs ~60% more query embeddings/calls.
4. **Do not claim Section Diversity improves quality.** Its effect is negligible
   in this experiment.
5. **Keep ContextAssembler available behind an explicit budget/precision policy,
   disabled by default.** Expansion gains coverage by buying substantial noise.
6. **Continue to reject the current Parent-Child configuration.** Low negative
   exposure does not compensate for missing gold and a 6.2x chunk index.

Sections 1–10 above describe the Dev-only tuning phase. The later Test run does
not retroactively change those experiments. The Test remains non-human-reviewed,
but is now agent-frozen and executed once under experiment
`20260728T115625Z-57404`. Its results support an offline held-out conclusion
only—not online effect or production A/B claims. See `FINAL-TEST-REPORT.md`.
