from __future__ import annotations

from collections import Counter

import numpy as np

from rag_lab.dataset.models import QuerySample
from rag_lab.models import StructuredDocument


class DatasetValidator:
  def validate(
    self,
    samples: list[QuerySample],
    documents: dict[str, StructuredDocument],
  ) -> list[str]:
    errors: list[str] = []
    ids = Counter(sample.id for sample in samples)
    questions = Counter(self._normalize(sample.question) for sample in samples)
    for sample in samples:
      if ids[sample.id] > 1:
        errors.append(f"{sample.id}: duplicate id")
      if questions[self._normalize(sample.question)] > 1:
        errors.append(f"{sample.id}: duplicate question")
      if not 5 <= len(sample.question) <= 300:
        errors.append(f"{sample.id}: invalid question length")
      if sample.answerable and not 1 <= len(sample.reference_answer) <= 5000:
        errors.append(f"{sample.id}: invalid answer length")
      if sample.answerable and not sample.evidences:
        errors.append(f"{sample.id}: answerable sample has no evidence")
      negative_ids = [evidence.id for evidence in sample.negative_evidences]
      if negative_ids != sample.negative_evidence_ids:
        errors.append(f"{sample.id}: negative evidence ids do not match embedded evidence")
      if set(negative_ids) & {evidence.id for evidence in sample.evidences}:
        errors.append(f"{sample.id}: gold evidence is also marked negative")
      for evidence in [*sample.evidences, *sample.negative_evidences]:
        document = documents.get(evidence.document_id)
        if document is None:
          errors.append(f"{sample.id}: document {evidence.document_id} does not exist")
          continue
        if evidence.end_offset > len(document.markdown) or evidence.start_offset >= evidence.end_offset:
          errors.append(f"{sample.id}: invalid evidence offset")
          continue
        restored = document.markdown[evidence.start_offset:evidence.end_offset]
        if restored != evidence.text:
          errors.append(f"{sample.id}: evidence text does not match offset")
    return errors

  @staticmethod
  def semantic_duplicates(
    samples: list[QuerySample],
    embeddings: np.ndarray,
    threshold: float,
  ) -> list[tuple[str, str, float]]:
    if len(samples) != len(embeddings):
      raise ValueError("Sample and embedding counts differ")
    normalized = embeddings / np.maximum(np.linalg.norm(embeddings, axis=1, keepdims=True), 1e-12)
    similarity = normalized @ normalized.T
    duplicates = []
    for left in range(len(samples)):
      for right in range(left + 1, len(samples)):
        score = float(similarity[left, right])
        if score > threshold:
          duplicates.append((samples[left].id, samples[right].id, score))
    return duplicates

  @staticmethod
  def _normalize(value: str) -> str:
    return " ".join(value.split()).casefold()
