# Phase 2 — Generation Evaluation Workbench

## Goal

Phase 1.5 answers **whether retrieval found the right evidence**. Phase 2 adds a
separate generation layer that answers **whether the final answer is useful and
faithful to the retrieved context**.

The retrieval metrics remain authoritative for retrieval. Generation metrics must
not be reported as retrieval gains.

## Evaluation flow

```text
Question
  -> existing chunking / embedding / exact retrieval
  -> Top-K source context
  -> generation prompt
  -> generated answer
  -> deterministic reference metrics
  -> optional LLM-as-a-Judge
  -> raw experiment JSON + comparison CSV
  -> Evaluation Workbench
```

Each generation artifact records:

- generation model and endpoint type;
- prompt `id`, `version`, full system/template text, and SHA-256 fingerprint;
- per-sample question, reference answer, assembled context, generated answer;
- generation latency;
- `ReferenceTokenPrecision`, `ReferenceTokenRecall`, and `ReferenceTokenF1`;
- optional judge scores for `correctness`, `completeness`, `faithfulness`, and
  `relevance`, plus an overall mean and unsupported-claim notes.

Reference-token metrics are diagnostic lexical metrics, not semantic correctness
claims. The Judge is also not ground truth: use a stable rubric/model and compare
its consistency on Dev before trusting deltas.

## Configure generation

Start from:

```text
configs/experiments/qwen-java-interview-phase2-workbench.yaml
```

The example uses an OpenAI-compatible endpoint so the lab can point at local
vLLM/Ollama-compatible gateways without coupling the experiment code to a vendor
SDK. Update `generation.provider.model` and `base_url` for the local gateway.

A separate stronger judge can be configured under `generation.judge.provider`.
If omitted, the generation provider is reused.

## Run one experiment from CLI

```bash
UV_CACHE_DIR=.uv-cache uv run python scripts/benchmark_chunking.py \
  --config configs/experiments/qwen-java-interview-phase2-workbench.yaml
```

For prompt iteration, prefer one chunk strategy at a time to avoid multiplying
LLM calls. The Workbench does this automatically when a strategy is selected.

## Launch the Workbench

Read-only historical comparison:

```bash
UV_CACHE_DIR=.uv-cache uv run python scripts/launch_workbench.py
```

Enable the Prompt experiment panel:

```bash
UV_CACHE_DIR=.uv-cache uv run python scripts/launch_workbench.py \
  --config configs/experiments/qwen-java-interview-phase2-workbench.yaml
```

Then open `http://127.0.0.1:8787` if the browser does not open automatically.

The UI supports:

- selecting any two historical `experiment_id + strategy` records;
- side-by-side metric values, absolute delta, and percentage delta;
- direction-aware highlighting for latency/waste/negative-exposure metrics;
- Prompt ID/version/hash and side-by-side Prompt text;
- editing the system prompt and user template;
- launching a Dev experiment from the selected baseline config;
- automatically loading the completed run as the candidate record.

The UI never overwrites the YAML file. Prompt changes are applied only to an
in-memory copy of the configured experiment.

## Test policy

The existing frozen Test policy remains unchanged. All UI-triggered experiments
still call `BenchmarkRunner`, so the one-time Test execution ledger and dataset
hash checks cannot be bypassed through the Workbench.

Prompt design, judge rubric changes, score-weight decisions, and model selection
must be performed on Dev/Hard Dev. Do not use the already executed frozen Test as
an iterative prompt-tuning set.

## Reading prompt deltas

A useful A/B comparison should keep everything except the intended variable
constant. For Prompt experiments, hold these fixed when possible:

- dataset version and split;
- chunk strategy;
- embedding model;
- retrieval Top-K;
- generation model and temperature;
- judge model and rubric.

Then compare at least:

- `JudgeCorrectness`;
- `JudgeCompleteness`;
- `JudgeFaithfulness`;
- `JudgeRelevance`;
- `ReferenceTokenF1` as a lexical diagnostic;
- `GenerationLatencyMs`;
- the existing retrieval metrics to confirm the retrieval layer did not change.

Do not collapse all dimensions into one weighted score until the individual
metrics and Judge stability have been reviewed on the Dev set.
