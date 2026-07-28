from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass

TOKEN_RE = re.compile(r"[A-Za-z0-9_./:+#-]+|[\u3400-\u9fff]|[^\s]", re.UNICODE)


@dataclass(frozen=True)
class TokenSpan:
  text: str
  start: int
  end: int


class LexicalApproxTokenizer:
  """Phase 1 regex tokenizer.

  This is a deterministic lexical approximation, not the Qwen tokenizer. It is
  retained to preserve existing chunk boundaries.
  """

  def spans(self, text: str) -> list[TokenSpan]:
    return [
      TokenSpan(match.group(), match.start(), match.end())
      for match in TOKEN_RE.finditer(text)
    ]

  def count(self, text: str) -> int:
    return len(self.spans(text))


def token_spans(text: str) -> list[TokenSpan]:
  return LexicalApproxTokenizer().spans(text)


def token_count(text: str) -> int:
  return LexicalApproxTokenizer().count(text)


def normalize_for_hash(text: str) -> str:
  return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text)).strip()


def text_hash(text: str) -> str:
  return hashlib.sha256(normalize_for_hash(text).encode("utf-8")).hexdigest()


def stable_id(prefix: str, *parts: object) -> str:
  payload = "\x1f".join(str(part) for part in parts)
  return f"{prefix}_{hashlib.sha1(payload.encode('utf-8')).hexdigest()[:16]}"
