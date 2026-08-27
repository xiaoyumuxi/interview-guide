from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ChatResponse:
  content: str
  raw: dict[str, Any]


class OpenAICompatibleChatProvider:
  """Minimal OpenAI-compatible chat client for local or remote model gateways."""

  def __init__(
    self,
    *,
    model: str,
    base_url: str,
    api_key_env: str | None = None,
    timeout_seconds: float = 120.0,
  ) -> None:
    self.model = model
    self.base_url = base_url.rstrip("/")
    self.api_key_env = api_key_env
    self.timeout_seconds = timeout_seconds

  @classmethod
  def from_config(cls, config: dict[str, Any]) -> "OpenAICompatibleChatProvider":
    if config.get("provider") != "openai_compatible":
      raise ValueError(f"Unsupported chat provider: {config.get('provider')}")
    return cls(
      model=str(config["model"]),
      base_url=str(config["base_url"]),
      api_key_env=config.get("api_key_env"),
      timeout_seconds=float(config.get("timeout_seconds", 120.0)),
    )

  def complete(
    self,
    *,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.0,
    response_format: dict[str, Any] | None = None,
  ) -> ChatResponse:
    payload: dict[str, Any] = {
      "model": self.model,
      "temperature": temperature,
      "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
      ],
    }
    if response_format is not None:
      payload["response_format"] = response_format

    headers = {"Content-Type": "application/json"}
    if self.api_key_env:
      api_key = os.environ.get(self.api_key_env)
      if not api_key:
        raise ValueError(f"Missing API key environment variable: {self.api_key_env}")
      headers["Authorization"] = f"Bearer {api_key}"

    request = urllib.request.Request(
      f"{self.base_url}/chat/completions",
      data=json.dumps(payload).encode("utf-8"),
      headers=headers,
      method="POST",
    )
    try:
      with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
        raw = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
      detail = exc.read().decode("utf-8", errors="replace")
      raise RuntimeError(f"Chat provider HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
      raise RuntimeError(f"Chat provider request failed: {exc.reason}") from exc

    choices = raw.get("choices") or []
    if not choices:
      raise RuntimeError("Chat provider returned no choices")
    content = choices[0].get("message", {}).get("content")
    if not isinstance(content, str) or not content.strip():
      raise RuntimeError("Chat provider returned empty content")
    return ChatResponse(content=content.strip(), raw=raw)
