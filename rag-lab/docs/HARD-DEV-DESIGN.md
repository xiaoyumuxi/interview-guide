# Hard Dev Design

## Purpose

Hard Dev supplements, but never modifies or replaces, the 80-sample Current Dev.
It tests implicit wording, scenario diagnosis, closely related terminology, and
multi-section completeness where Top-5 retrieval is not already near a trivial
ceiling. It is a tuning split only.

The target is 48 samples: four per corpus category across the same twelve Java
backend categories used in Phase 1.

## Evidence boundary

Every gold and negative evidence object must be copied byte-for-byte from the
Current Dev evidence pool. A sample may combine Dev evidence only when the
sections have an explicit technical relationship. No Test evidence, Test answer,
or Test question may be used to author a sample.

Automated release checks compare Hard Dev with the Test candidate for:

- evidence content hashes;
- identical document sections;
- overlapping source offsets;
- identical reference answers;
- exact and normalized question collisions.

The audit is allowed to read Test metadata and spans, but neither embeds Test
questions nor performs retrieval on Test.

## Difficulty dimensions

Each sample records one of:

- `IMPLICIT_PARAPHRASE`
- `SCENARIO_DIAGNOSIS`
- `CONSTRAINT_BASED_SELECTION`
- `CODE_BEHAVIOR`
- `TERMINOLOGY_DISAMBIGUATION`
- `MULTI_SECTION_REASONING`
- `VERSION_IMPLEMENTATION_DIFFERENCE`

Questions must resemble real interview follow-ups, avoid copying headings, and
must not reveal the answer by listing every decisive keyword. Reference answers
are concise evidence-only summaries. Negative evidence, when present, comes from
the same concept cluster and is plausible but wrong for the asked distinction.

## Review protocol

An authoring agent produces `hard-dev-draft.jsonl` with
`PENDING_AGENT_REVIEW`. A separate agent context reviews every item for:

```text
question_naturalness, evidence_grounding, answer_grounding, difficulty,
gold_uniqueness, negative_quality, multi_section_relation, offset_replay,
test_leakage
```

First-pass failures are written as `REJECT`. Revised items must be re-reviewed
from an independent context before release. The final label is
`AGENT_REVIEWED_NOT_HUMAN`; it must never be described as human review.

The Test candidate remains non-human-reviewed, unfrozen, and `NOT EXECUTED`.
