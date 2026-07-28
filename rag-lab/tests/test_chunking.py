from pathlib import Path

from rag_lab.chunking import FixedChunker, ParentChildChunker, StructureAwareChunker
from rag_lab.common.text import token_spans
from rag_lab.models import NodeType
from rag_lab.parsing import MarkdownStructureParser

FIXTURE = Path(__file__).parent / "fixtures/golden.md"


def _document():
  return MarkdownStructureParser().parse("golden", FIXTURE.read_text(encoding="utf-8"))


def test_fixed_chunk_offsets_and_overlap() -> None:
  document = _document()
  chunks = FixedChunker(chunk_size=20, overlap=5).chunk(document)
  assert len(chunks) > 1
  for chunk in chunks:
    assert document.markdown[chunk.start_offset:chunk.end_offset] == chunk.text
  first_tokens = {token.text for token in token_spans(chunks[0].text)}
  second_start = [token.text for token in token_spans(chunks[1].text)[:5]]
  assert set(second_start) <= first_tokens
  assert chunks[0].next_id == chunks[1].id


def test_structure_chunker_never_emits_heading_only_chunk() -> None:
  chunks = StructureAwareChunker(max_tokens=40).chunk(_document())
  assert chunks
  assert all(chunk.text.strip() for chunk in chunks)
  assert all(not chunk.text.lstrip().startswith("#") for chunk in chunks)
  code_text = next(block.text for block in _document().blocks
                   if block.node_type == NodeType.CODE_BLOCK)
  assert any("acknowledge" in chunk.text for chunk in chunks)
  assert code_text.strip() in "\n".join(chunk.text for chunk in chunks)


def test_parent_child_uses_real_sections_and_children_point_to_parents() -> None:
  chunks = ParentChildChunker(child_max_tokens=30).chunk(_document())
  parents = {chunk.id: chunk for chunk in chunks if chunk.metadata["role"] == "parent"}
  children = [chunk for chunk in chunks if chunk.metadata["role"] == "child"]
  assert parents and children
  assert all(child.parent_id in parents for child in children)
  assert all(
    parents[child.parent_id].start_offset <= child.start_offset < child.end_offset
    <= parents[child.parent_id].end_offset
    for child in children
  )


def test_large_table_chunks_repeat_header() -> None:
  markdown = "# T\n\n| key | value |\n| --- | --- |\n" + "".join(
    f"| row-{index} | value-{index} |\n" for index in range(10)
  )
  document = MarkdownStructureParser().parse("table", markdown)
  chunks = StructureAwareChunker(max_tokens=20).chunk(document)
  table_chunks = [chunk for chunk in chunks if chunk.metadata.get("synthetic_table_header")]
  assert len(table_chunks) > 1
  assert all(chunk.text.startswith("| key | value |") for chunk in table_chunks)
