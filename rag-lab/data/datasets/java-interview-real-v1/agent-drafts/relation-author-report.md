# relation_qa_author report

Status: PASS

No local or remote generation model was called. All questions and concise reference answers were authored directly from fixed upstream Markdown evidence.

## Output

- MULTI_SECTION: 25
- HARD_NEGATIVE: 25
- Total: 50
- review_status: AGENT_REVIEWED on all rows
- validation.author_task: relation_qa_author on all rows

## Validation

- Pydantic schema reload: PASS (50 rows)
- DatasetValidator strict exact replay: PASS (83 gold + 50 embedded negative Evidence spans)
- Exact support quote checks: PASS (188 quotes)
- Hard-negative top-level embedding: PASS (50 complete Evidence objects; IDs match negative_evidence_ids)
- Hard-negative strict exact replay: PASS (50/50 negative Evidence spans)
- Unique sample IDs: PASS (50/50)
- Unique normalized questions: PASS (50/50)
- MULTI_SECTION evidence cardinality: PASS (all rows have at least 2 real spans)
- HARD_NEGATIVE cardinality: PASS (all rows have exactly 2 distinct non-gold spans)
- Logical relation review: PASS (only curated same-topic relations)
- Hard-negative concept-cluster review: PASS (each negative includes a reason_not_answer audit note)
- Evidence-bounded answer audit: PASS after correcting relation_multi_005,
  relation_multi_011, relation_hard_negative_008, and
  relation_hard_negative_023

## Release Review Corrections

- `relation_multi_005` no longer claims a G1 concurrent-marking phase that was
  not directly stated by its selected G1 Evidence.
- `relation_hard_negative_022` now uses unused user/kernel-thread-model and
  fiber/coroutine/virtual-thread sections. Neither span, alone or combined,
  provides the requested shared-versus-private resource inventory.
- `relation_hard_negative_023` replaces the epoll span that directly exposed
  select's O(N) contrast with an unused LT/ET notification-semantics section.
  The two retained negatives still belong to the I/O-multiplexing cluster but
  do not jointly explain all three requested select limitations.

## Relation coverage

- cache-avalanche: 1
- cache-avalanche-penetration-breakdown-key-scope: 1
- cache-avalanche-penetration-breakdown-mitigation: 1
- cache-avalanche-penetration-breakdown-trigger: 1
- cache-breakdown: 1
- cache-penetration: 1
- cms-vs-g1-algorithm-and-fragmentation: 1
- cms-vs-g1-jdk-lifecycle: 1
- cms-vs-g1-pause-control: 1
- concurrenthashmap-jdk8: 1
- condition-notification: 1
- distributed-lock-zookeeper: 1
- hashmap-concurrency: 1
- hashmap-vs-concurrenthashmap-concurrent-write: 1
- hashmap-vs-concurrenthashmap-structure: 1
- http11-connection: 1
- http11-vs-http2-connection-reuse: 1
- http11-vs-http2-transport-features: 1
- http2-multiplexing: 1
- io-multiplexing-select: 1
- java-lock-capabilities: 1
- java-lock-implementation: 1
- jvm-gc-cms: 1
- jvm-gc-g1: 1
- jvm-gc-g1-phases: 1
- message-reliability-kafka: 1
- optimistic-lock-cas: 1
- optimistic-lock-longadder: 1
- optimistic-vs-pessimistic-lock-assumption: 1
- optimistic-vs-pessimistic-lock-workload: 1
- os-process-resources: 1
- os-thread-resources: 1
- poll-vs-epoll: 1
- process-vs-thread-cost-and-concurrency: 1
- process-vs-thread-resources: 1
- rdb-vs-aof-combined-selection-and-recovery: 1
- rdb-vs-aof-recording-model: 1
- rdb-vs-aof-runtime-cost-and-loss-window: 1
- redis-persistence-aof: 1
- redis-persistence-aof-fsync: 1
- redis-persistence-rdb: 1
- redis-persistence-recovery: 1
- redis-vs-zookeeper-distributed-lock-acquire: 1
- redis-vs-zookeeper-distributed-lock-failure: 1
- select-vs-poll: 1
- spring-ioc-vs-aop: 1
- synchronized-lock-target: 1
- synchronized-vs-reentrantlock-implementation-and-capability: 1
- synchronized-vs-reentrantlock-reentrancy: 1
- synchronized-vs-reentrantlock-release-and-notification: 1

## Provenance boundary

- Source manifest rows: 48
- Parsed upstream Markdown documents: 48
- Offset-aware evidence catalog entries: 1267
- Source files came only from the materialized java-interview-real-v1 Markdown corpus and its manifest.
- Gold and negative Evidence text equals normalized markdown[start_offset:end_offset] exactly, including boundary whitespace.
- Evidence text is verbatim; reference answers are short evidence-bounded summaries.
