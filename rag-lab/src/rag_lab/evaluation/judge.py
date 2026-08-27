from __future__ import annotations

import json
import re
from typing import Any

from rag_lab.generation.providers import OpenAICompatibleChatProvider

JUDGE_SYSTEM_PROMPT = """You are a strict RAG answer evaluator. Judge only from the supplied question,
reference answer, and retrieved context. Return JSON only. Score each dimension from 0 to 5:
correctness: factual agreement with the reference answer;
completeness: coverage of important reference points;
faithfulness: claims supported by retrieved context;
relevance: directness and usefulness for the question.
Also return a concise reason string and unsupported_claims as a list of short strings.
"""


def judge_answer(
  provider: OpenAICompatibleChatProvider,
  *,
  question: str,
  reference_answer: str,
  context: str,
  answer: str,
  temperature: float = 0.0,
) -> dict[str, Any]:
  user_prompt = (
    f"QUESTION:\n{question}\n\n"
    f"REFERENCE ANSWER:\n{reference_answer}\n\n"
    f"RETRIEVED CONTEXT:\n{context}\n\n"
    f"CANDIDATE ANSWER:\n{answer}\n\n"
    "Return an object with correctness, completeness, faithfulness, relevance, "
    "reason, unsupported_claims."
  )
  response = provider.complete(
    system_prompt=JUDGE_SYSTEM_PROMPT,
    user_prompt=user_prompt,
    temperature=temperature,
    response_format={"type": "json_object"},
  )
  parsed = _parse_json_object(response.content)
  scores = {
    key: _clamp_score(parsed.get(key))
    for key in ("correctness", "completeness", "faithfulness", "relevance")
  }
  scores["overall"] = sum(scores.values()) / len(scores)
  scores["reason"] = str(parsed.get("reason", "")).strip()
  unsupported = parsed.get("unsupported_claims") or []
  scores["unsupported_claims"] = [str(item) for item in unsupported] if isinstance(unsupported, list) else []
  return scores


def _parse_json_object(text: str) -> dict[str, Any]:
  try:
    value = json.loads(text)
  except json.JSONDecodeError:
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
      raise ValueError("Judge response does not contain a JSON object")
    value = json.loads(match.group(0))
  if not isinstance(value, dict):
    raise ValueError("Judge response must be a JSON object")
  return value


def _clamp_score(value: Any) -> float:
  try:
    numeric = float(value)
  except (TypeError, ValueError) as exc:
    raise ValueError(f"Invalid judge score: {value!r}") from exc
  return min(5.0, max(0.0, numeric))
