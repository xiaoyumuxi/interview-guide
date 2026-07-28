# Split Audit

> This document records the pre-freeze audit state. The candidate was later
> independently agent-reviewed, frozen as `AGENT_REVIEWED_NOT_HUMAN`, and
> executed exactly once. See `FINAL-TEST-REPORT.md`.

## Status

- Current Dev: 80 samples, agent-reviewed, tuning allowed.
- Test candidate: 40 samples, agent-reviewed but **not human-reviewed**, not frozen.
- Phase 1.5 Test execution: **NOT EXECUTED**.

This audit reads Test metadata, questions, answers, and evidence spans only to
measure split composition and leakage. It does not embed Test queries, retrieve
for them, tune with them, or produce Test metrics.

## Distribution

Query types were stratified almost proportionally:

| Query type | Dev | Test candidate |
|---|---:|---:|
| Direct fact | 21 | 11 |
| Paraphrase | 19 | 9 |
| Terminology | 12 | 6 |
| Multi-section | 12 | 6 |
| Hard negative | 9 | 5 |
| Unanswerable | 7 | 3 |

The domain distribution is not IID:

| Category | Dev | Test candidate |
|---|---:|---:|
| distributed | 9 | 1 |
| java-basics | 8 | 1 |
| java-collections | 14 | 1 |
| juc | 18 | 1 |
| jvm | 3 | 7 |
| message-queue | 6 | 1 |
| mysql | 3 | 5 |
| network | 2 | 11 |
| operating-system | 10 | 1 |
| redis | 3 | 9 |
| spring | 6 | 4 |
| system-design | 10 | 1 |

Test is concentrated in network, Redis, JVM, and MySQL, while Dev is
concentrated in JUC, collections, operating systems, and system design.

Gold-evidence repository counts are also shifted:

| Repository | Dev evidence | Test evidence |
|---|---:|---:|
| JavaGuide | 74 | 41 |
| advanced-java | 18 | 2 |

Dev gold evidence spans 27 documents and Test spans 19; 13 document IDs occur in
both splits, but their selected sections are disjoint.

## Leakage checks

Across all gold and embedded negative evidence:

- identical `(document_id, start_offset, end_offset)`: 0
- identical evidence text SHA-256: 0
- identical `(document_id, heading_path)` section: 0
- overlapping source spans: 0

The split is therefore clean at evidence and section level, while sharing some
source documents. Sharing a document is acceptable because the selected
sections do not overlap, but it should remain an explicit audit dimension.

## Interpretation

The current 40 samples are best described as a **Domain-Shift Test Candidate**,
not an IID Test. Their value is measuring robustness under a domain mix different
from Dev, but that makes them unsuitable as the only final test for a general
Java backend claim.

No split is changed in Phase 1.5. A future release can create two separately
human-reviewed and frozen sets:

1. **IID Test**: category, repository, query-type, and document distributions
   approximately matched to Dev.
2. **Domain-Shift Test**: intentionally concentrated in underrepresented or
   operational domains, with the shift declared before execution.

Both should be grouped by evidence section and semantic question cluster before
sampling, then manually reviewed, frozen, and executed once.
