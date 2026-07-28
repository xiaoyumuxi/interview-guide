# java-interview-real-v1 Test Final Freeze Review

## Review identity

- Reviewer: `final_test_freeze_reviewer`
- Review kind: `AGENT_REVIEWED_NOT_HUMAN`
- Human review: `false`
- Input: `test-agent-reviewed.jsonl`
- Scope: 40 Test samples
- Benchmark/retrieval executed during review: `false`
- Samples modified during review: `false`

This is an independent agent review performed as a final pre-freeze gate. It must not be described as human review.

## Result

- APPROVE: 40
- REJECT: 0
- Final decision: **PASS — eligible for agent-reviewed freeze**

All 40 samples passed the requested checks:

- question naturalness
- evidence grounding
- answer grounding
- gold uniqueness
- hard-negative quality
- multi-section relation
- source-offset replay
- provenance
- unanswerable validity

The per-sample record is `test-final-freeze-decisions.jsonl`.

## Mechanical verification

- Test sample count: 40
- Answerable samples: 37
- Unanswerable samples: 3
- Gold Evidence count: 43
- Negative Evidence count: 10
- Offset replay: 53/53 exact matches
- File SHA-256 verification: 53/53 matches
- Repository Commit verification: 53/53 matches
- Provenance field verification: 53/53 complete and consistent
- Sample IDs: unique
- Questions: unique

Offsets were replayed against `data/markdown/java-interview-real-v1/<document_id>/normalized.md` using Unicode code-point indexing, matching the Python dataset implementation.

Pinned source repositories:

- JavaGuide: `8fb36af2bcd92d87c5223214980a9a97ef946f10`, Apache-2.0
- advanced-java: `1659850d7de4739ac9394dddd6c68466a8c38761`, CC-BY-SA-4.0

## Semantic review summary

The 37 answerable samples use answers that are concise summaries of the supplied Evidence. No reviewed answer requires knowledge outside its Gold Evidence.

The six Multi-Section samples use genuine relationships:

- CMS versus G1: fragmentation behavior and pause-control design
- RDB versus AOF: recorded material, freshness, runtime overhead, and loss window
- HTTP/1.1 versus HTTP/2: connection reuse, multiplexing granularity, and head-of-line blocking

The five Hard Negative samples use near-neighbor evidence from the same concept clusters:

- CMS/G1/ZGC/ParNew garbage collectors
- RDB/AOF persistence mechanisms
- HTTP connection reuse, range requests, and HTTPS/TLS

The negative sections are semantically close enough to be difficult but do not correctly answer their corresponding questions. Gold Evidence remains uniquely sufficient.

The three unanswerable topics—ClickHouse MergeTree parts merging, eBPF verifier loop termination, and Istio ambient mesh ztunnel—are absent from the pinned corpus. Their empty Evidence and refusal answers are valid.

## Freeze boundary

This report approves the current Test file for an **agent-reviewed freeze** only. It does not claim human review. Any later mutation of the Test JSONL, source manifest, pinned source files, or offset-normalized Markdown invalidates this review and requires a new decision file.
