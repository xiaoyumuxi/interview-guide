from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class QueryType(StrEnum):
  DIRECT_FACT = "DIRECT_FACT"
  PARAPHRASE = "PARAPHRASE"
  TERMINOLOGY = "TERMINOLOGY"
  MULTI_SECTION = "MULTI_SECTION"
  HARD_NEGATIVE = "HARD_NEGATIVE"
  UNANSWERABLE = "UNANSWERABLE"


class Evidence(BaseModel):
  id: str
  document_id: str
  heading_path: list[str]
  start_offset: int = Field(ge=0)
  end_offset: int = Field(gt=0)
  text: str
  metadata: dict[str, Any] = Field(default_factory=dict)


class QuerySample(BaseModel):
  id: str
  question: str
  reference_answer: str
  evidences: list[Evidence]
  type: QueryType
  difficulty: str = "MEDIUM"
  answerable: bool = True
  negative_evidence_ids: list[str] = Field(default_factory=list)
  negative_evidences: list[Evidence] = Field(default_factory=list)
  split: str | None = None
  generator_model: str | None = None
  review_status: str = "UNREVIEWED"
  validation: dict[str, Any] = Field(default_factory=dict)
