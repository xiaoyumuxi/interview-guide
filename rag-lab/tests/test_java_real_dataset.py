from rag_lab.dataset.java_real_builder import (
  SectionEvidenceSampler,
  clean_heading,
  extractive_summary,
  is_natural_question,
)
from rag_lab.ingestion import MarkdownNormalizer
from rag_lab.parsing import MarkdownStructureParser


def _document():
  markdown = MarkdownNormalizer().normalize(
    """
# Java 并发

## ReentrantLock

ReentrantLock 支持可中断获取锁、公平锁以及多个 Condition，适合需要高级锁能力的场景。
调用方需要显式释放锁，并通过 try-finally 保证异常路径也能够正确完成释放。

## synchronized

synchronized 由 JVM 管理锁的获取与释放，代码离开同步块时会自动释放监视器锁。
它的语法直接作用于方法或代码块，适合锁行为与词法作用域一致的场景。
"""
  )
  return MarkdownStructureParser().parse("locks-123", markdown)


def test_section_evidence_is_verbatim_and_carries_source_metadata() -> None:
  document = _document()
  metadata = {
    document.document_id: {
      "repository": "JavaGuide",
      "relative_path": "docs/java/concurrent/locks.md",
      "category": "juc",
      "file_sha256": "abc",
    },
  }
  evidences = SectionEvidenceSampler(min_tokens=5).sample([document], metadata)
  assert len(evidences) == 2
  for evidence in evidences:
    restored = document.markdown[evidence.start_offset:evidence.end_offset]
    assert restored == evidence.text
    assert evidence.metadata["repository"] == "JavaGuide"


def test_upstream_heading_is_used_as_natural_question() -> None:
  document = _document()
  heading = clean_heading(document.blocks[1].heading_path[-1])
  assert heading == "ReentrantLock"
  assert not is_natural_question(heading)


def test_extractive_summary_only_uses_verbatim_support_quotes() -> None:
  document = _document()
  evidence = SectionEvidenceSampler(min_tokens=5).sample(
    [document],
    {document.document_id: {"repository": "JavaGuide", "category": "juc"}},
  )[0]
  summary = extractive_summary(evidence.text, "ReentrantLock 支持哪些锁能力？", 1)
  assert summary is not None
  answer, quotes = summary
  assert quotes[0] in evidence.text
  assert answer != evidence.text
  assert "interrupt()" not in answer
