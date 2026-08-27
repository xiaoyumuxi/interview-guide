# Changelog

## 2026-08-27 — Phase 2 generation evaluation workbench

- Added an optional generation stage after retrieval so one experiment can record
  retrieval quality, answer quality, prompt identity, generation latency, and judge
  scores without changing Phase 1.5 retrieval behavior when generation is disabled.
- Added deterministic reference-token precision/recall/F1 and an optional
  LLM-as-a-Judge rubric for correctness, completeness, faithfulness, and relevance.
- Added SHA-256 prompt fingerprints with prompt ID/version so prompt changes are
  traceable across experiment artifacts and comparison CSVs.
- Added a local Evaluation Workbench that scans `results/raw`, compares arbitrary
  experiment/strategy pairs, shows metric deltas and Prompt differences, and can
  launch a Dev prompt experiment from a configured baseline.
- Prompt experiments still execute through `BenchmarkRunner`; the existing frozen
  Test execution guard is unchanged and cannot be bypassed from the Workbench.

## 2026-07-28 — Agent-reviewed Test freeze and one-time run

- Added an independent 40/40 agent review with 53/53 exact Evidence replay checks.
- Froze Test as `AGENT_REVIEWED_NOT_HUMAN`; `human_reviewed` remains false.
- Added immutable dataset/decision hashes and a one-time execution ledger.
- Ran local Qwen3-Embedding-0.6B + exact cosine Test once as experiment
  `20260728T115625Z-57404`; repeated execution is refused.
- Added the final Test report and comparison CSV. No Test-driven optimization was
  performed after execution.

## 2026-07-28 — Phase 1.5 audit fixes

- Fixed hard-negative CSV identity fields being overwritten by empty metric values.
- Added `NEGATIVE_BEARING` derived evaluation group and effective mapping/pairwise
  denominators.
- Added explicit lexical-approximate and local Hugging Face Qwen token counters;
  existing chunk boundaries remain unchanged.
- Added isolated cold-cache and uniformly preloaded warm-cache ablation performance
  measurements.
- Added complete shared experiment metadata with top-level `test_executed=false`.
- Documented Hard Query Dev as a Dev-evidence-based query stress set rather than
  an independent generalization evaluation.
- Added audit regression tests, fix report, token comparison, performance reports,
  and an updated ablation raw artifact while preserving original quality metrics.
