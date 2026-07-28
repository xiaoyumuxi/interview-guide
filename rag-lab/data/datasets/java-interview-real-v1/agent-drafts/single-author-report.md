# java-interview-real-v1 Single-Evidence Author Report

## Scope

- Author task: `single_qa_author`
- Output: `single.jsonl`
- Corpus: 48 Markdown documents fixed by
  `data/corpus/java-interview-real-v1/manifest.jsonl`
- Generation model: none
- Question source: upstream Markdown headings, with manual selection and natural
  interview-style rewrites where needed
- Answer source: concise summaries grounded only in one verbatim evidence span

## Distribution

| Type | Count |
|---|---:|
| `DIRECT_FACT` | 50 |
| `PARAPHRASE` | 40 |
| `TERMINOLOGY` | 25 |
| `UNANSWERABLE` | 15 |
| **Total** | **130** |

The 115 answerable samples contain exactly one evidence span each. The 15
`UNANSWERABLE` samples intentionally contain no evidence and use the fixed answer
“当前语料没有足够证据回答该问题。”

## Authoring Method

1. Loaded the selected upstream Markdown directly from
   `data/corpus/java-interview-real-v1`, then applied the repository's
   conservative Markdown normalizer and offset-aware parser.
2. Sampled body sections with `SectionEvidenceSampler`; navigation, promotion,
   link-list, and undersized sections were excluded by the existing corpus
   filters.
3. Used upstream question headings whenever they already sounded like Java
   backend interview questions. Rephrasing was limited to removing editorial
   wording and making the prompt natural; no “根据文档” template was used.
4. Wrote each reference answer as a concise, evidence-only summary. No external
   fact was added, and no answer copies its complete evidence span.
5. Added one or more verbatim short excerpts to
   `validation.support_quotes`. Every excerpt occurs byte-for-byte in that
   sample's evidence text.
6. Marked every row `review_status=AGENT_REVIEWED` and
   `validation.author_task=single_qa_author`.

## Validation Results

| Check | Result |
|---|---:|
| Pydantic/schema validation | 130 / 130 PASS |
| Exact type quotas | PASS |
| Unique IDs | 130 / 130 PASS |
| Unique normalized questions | 130 / 130 PASS |
| Answerable rows with exactly one evidence | 115 / 115 PASS |
| Evidence offset replay against normalized source | 115 / 115 PASS |
| Evidence provenance metadata completeness | 115 / 115 PASS |
| Verbatim support quote containment | 277 / 277 PASS |
| Answer differs from complete evidence span | 115 / 115 PASS |
| Unanswerable rows without evidence | 15 / 15 PASS |
| `generator_model` is null | 130 / 130 PASS |
| Templated “根据文档” questions | 0 |

Evidence metadata includes repository name and URL, fixed commit, license,
relative path, file SHA-256, and category, copied from the corpus manifest.
Offsets use the half-open interval `[start_offset, end_offset)`. Evidence text is
the exact `markdown[start_offset:end_offset]` slice, including trailing line
breaks present inside the interval.

## Audit Revision

The draft was revised after a second content audit. Type counts and IDs were
kept stable.

- Completed the five Kafka term definitions in sample 020.
- Replaced answers that equaled their complete evidence spans in samples 032,
  048, and 095 with concise supported summaries.
- Replaced sample 034's deleted `String` statement with a grounded `hashCode`
  efficiency question.
- Narrowed sample 042 to the reason CLH queues organize competing threads and
  added the starvation/ordering evidence.
- Replaced sample 053 with the
  `@EnableAutoConfiguration`/`AutoConfigurationImportSelector` mechanism.
- Completed the MyISAM/InnoDB comparison, DATETIME/TIMESTAMP selection rule,
  non-repeatable-read/phantom-read definitions, ArrayList insertion/deletion
  complexities, fair/non-fair lock comparison, `@Transactional` scopes, and the
  four SQL isolation-level names.
- Removed the corrected C++ threading claim from sample 066 and retained only
  uncontroversial Java characteristics.
- Narrowed broad questions in samples 027, 037, 043, 046, 065, 070, 084, and
  109 so one evidence span fully answers each question.
- Replaced sample 045 with the CPU-bound versus I/O-bound single-core tradeoff,
  and sample 106 with the current-read versus snapshot-read distinction.
- Cleaned editorial, colloquial, dangling, and link-oriented answer text in
  samples 003, 007, 008, 021, 028, 035, 076, 097, 099, and 101.
- Expanded support quotes for samples 019, 026, 040, 059, 069, 096, and 100 to
  full supporting sentences, bullets, or table rows.
- Replaced the answerable GraalVM question in sample 116 with a PostgreSQL
  logical-replication-slot question. The terms `confirmed_flush_lsn`,
  `restart_lsn`, and `replication slot` have zero occurrences across all 48
  selected documents.
- Re-materialized all 115 answerable evidence texts as exact half-open offset
  slices after the validator adopted strict, non-trimming replay semantics.

## Diversity Revision

The third authoring pass replaced high-density samples with manually authored
questions from previously unused real Markdown sections. IDs and type quotas
were kept stable; no LLM was used.

### Replaced IDs

- Topic-diversity replacements:
  `002`, `005`, `012`, `013`, `027`, `028`, `036`, `037`, `046`, `056`,
  `067`, `068`, `070`, `081`, `093`, and `103`.
- Historical relation-overlap replacements:
  `006`, `009`, `010`, `018`, `019`, `039`, and `059`.

The 16 topic-diversity replacements add four answerable samples to each of
`distributed`, `system-design`, `message-queue`, and `network`. The seven
additional replacements remove all pre-existing Evidence-ID and heading-section
overlap with `relations.jsonl`.

### Final Category Distribution

| Category | Answerable samples |
|---|---:|
| `java-basics` | 18 |
| `java-collections` | 12 |
| `juc` | 19 |
| `jvm` | 4 |
| `spring` | 10 |
| `mysql` | 13 |
| `redis` | 11 |
| `network` | 10 |
| `operating-system` | 3 |
| `distributed` | 4 |
| `message-queue` | 7 |
| `system-design` | 4 |
| **Total answerable** | **115** |

### Target Category Coverage

| Category | Samples | Documents | Unique sections | Repository distribution |
|---|---:|---:|---:|---|
| `distributed` | 4 | 2 | 4 | advanced-java: 4 |
| `system-design` | 4 | 2 | 4 | advanced-java: 4 |
| `message-queue` | 7 | 3 | 7 | JavaGuide: 5; advanced-java: 2 |
| `network` | 10 | 2 | 10 | JavaGuide: 10 |

The full answerable set uses 105 JavaGuide evidence spans and 10 advanced-java
evidence spans. All 115 evidence IDs are unique, all 115
`(document_id, heading_path)` section keys are unique, and their intersections
with all gold and embedded hard-negative Evidence IDs and section keys in
`relations.jsonl` are both empty.

## Final Content Audit

Four answer-completeness issues were corrected without changing IDs, types,
Evidence spans, offsets, or quotas:

- `071` now covers invocation style and distinguishes direct instance-member
  access from access through an explicit object reference.
- `080` now covers the selection criteria for `Map`, `Set`, and `List`.
- `087` now states that, strictly speaking, thread creation ultimately uses
  `new Thread().start()`.
- `115` now includes the key three-way-close condition: the passive closer has
  no pending data and its application immediately closes the connection,
  allowing ACK and FIN to be combined.

## Release Review Corrections

- `050` and `052` were rewritten as concise evidence summaries instead of
  closely following the source sentences.
- `057` now includes the lower `TIMESTAMP` boundary
  (`1970-01-01 00:00:01.000000` UTC), as well as the upper 2038 boundary.
- `071` now says a static method cannot directly access instance members while
  making clear that it can access them through an object reference.

## Review Boundary

`AGENT_REVIEWED` records the authoring and mechanical grounding review performed
for this draft. It does not represent the separate human review required before
freezing the final 40-row test set.
