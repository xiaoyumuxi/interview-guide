from __future__ import annotations

import hashlib
import re
import statistics
import time
from typing import Any

from rag_lab.dataset.models import QuerySample
from rag_lab.evaluation.judge import judge_answer
from rag_lab.generation.providers import OpenAICompatibleChatProvider
from rag_lab.retrieval.exact import SearchResult

DEFAULT_SYSTEM_PROMPT = (
  "Answer the interview question using only the retrieved context. "
  "If the context is insufficient, say so explicitly."
)
DEFAULT_USER_TEMPLATE = "Question:\n{question}\n\nRetrieved context:\n{context}\n\nAnswer:"


def run_generation(
  *,
  samples: list[QuerySample],
  results: dict[str, list[SearchResult]],
  config: dict[str, Any],
) -> dict[str, Any]:
  provider = OpenAICompatibleChatProvider.from_config(config["provider"])
  prompt = config.get("prompt", {})
  system_prompt = str(prompt.get("system", DEFAULT_SYSTEM_PROMPT))
  template = str(prompt.get("template", DEFAULT_USER_TEMPLATE))
  prompt_meta = prompt_metadata(prompt, system_prompt=system_prompt, template=template)
  top_k = int(config.get("top_k", 5))
  temperature = float(config.get("temperature", 0.0))
  judge_config = config.get("judge", {})
  judge_enabled = bool(judge_config.get("enabled", False))
  judge_provider = (
    OpenAICompatibleChatProvider.from_config(judge_config.get("provider", config["provider"]))
    if judge_enabled else None
  )

  rows: dict[str, dict[str, Any]] = {}
  metric_rows: list[dict[str, float]] = []
  for sample in samples:
    if not sample.answerable:
      continue
    context = assemble_context(results[sample.id], top_k)
    user_prompt = render_prompt(template, question=sample.question, context=context)
    started = time.perf_counter()
    response = provider.complete(
      system_prompt=system_prompt,
      user_prompt=user_prompt,
      temperature=temperature,
    )
    latency_ms = (time.perf_counter() - started) * 1000
    lexical = reference_metrics(response.content, sample.reference_answer)
    row: dict[str, Any] = {
      "question": sample.question,
      "reference_answer": sample.reference_answer,
      "context": context,
      "answer": response.content,
      "latency_ms": latency_ms,
      "reference_metrics": lexical,
    }
    metrics = dict(lexical)
    if judge_provider is not None:
      judge = judge_answer(
        judge_provider,
        question=sample.question,
        reference_answer=sample.reference_answer,
        context=context,
        answer=response.content,
        temperature=float(judge_config.get("temperature", 0.0)),
      )
      row["judge"] = judge
      for key in ("correctness", "completeness", "faithfulness", "relevance", "overall"):
        metrics[f"Judge{key.title()}"] = float(judge[key])
    row["metrics"] = metrics
    rows[sample.id] = row
    metric_rows.append({**metrics, "GenerationLatencyMs": latency_ms})

  return {
    "provider": {
      "type": config["provider"].get("provider"),
      "model": config["provider"].get("model"),
      "base_url": config["provider"].get("base_url"),
    },
    "prompt": prompt_meta,
    "top_k": top_k,
    "judge_enabled": judge_enabled,
    "metrics": {"Overall": aggregate_metrics(metric_rows)},
    "samples": rows,
  }


def assemble_context(ranked: list[SearchResult], top_k: int) -> str:
  sections: list[str] = []
  seen: set[str] = set()
  for result in ranked[:top_k]:
    chunk = result.chunk
    if chunk.id in seen:
      continue
    seen.add(chunk.id)
    heading = " > ".join(chunk.heading_path)
    label = f"[{chunk.document_id}]" + (f" {heading}" if heading else "")
    sections.append(f"{label}\n{chunk.source_text or chunk.text}".strip())
  return "\n\n---\n\n".join(sections)


def render_prompt(template: str, *, question: str, context: str) -> str:
  return template.replace("{question}", question).replace("{context}", context)


def prompt_metadata(
  prompt: dict[str, Any],
  *,
  system_prompt: str,
  template: str,
) -> dict[str, Any]:
  canonical = f"{system_prompt}\n---USER---\n{template}"
  return {
    "id": str(prompt.get("id", "default")),
    "version": str(prompt.get("version", "v1")),
    "sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    "system": system_prompt,
    "template": template,
  }


def reference_metrics(answer: str, reference: str) -> dict[str, float]:
  answer_tokens = _tokens(answer)
  reference_tokens = _tokens(reference)
  if not answer_tokens or not reference_tokens:
    return {"ReferenceTokenPrecision": 0.0, "ReferenceTokenRecall": 0.0, "ReferenceTokenF1": 0.0}
  answer_counts = _counts(answer_tokens)
  reference_counts = _counts(reference_tokens)
  overlap = sum(min(answer_counts.get(token, 0), count) for token, count in reference_counts.items())
  precision = overlap / len(answer_tokens)
  recall = overlap / len(reference_tokens)
  f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
  return {
    "ReferenceTokenPrecision": precision,
    "ReferenceTokenRecall": recall,
    "ReferenceTokenF1": f1,
  }


def aggregate_metrics(rows: list[dict[str, float]]) -> dict[str, float]:
  if not rows:
    return {}
  keys = sorted({key for row in rows for key in row})
  return {
    key: statistics.fmean(float(row[key]) for row in rows if key in row)
    for key in keys
  }


def _tokens(text: str) -> list[str]:
  return [token.lower() for token in re.findall(r"[A-Za-z0-9_+#.-]+|[\u4e00-\u9fff]", text)]


def _counts(tokens: list[str]) -> dict[str, int]:
  output: dict[str, int] = {}
  for token in tokens:
    output[token] = output.get(token, 0) + 1
  return output
