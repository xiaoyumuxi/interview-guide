from pathlib import Path

from rag_lab.ingestion import MarkdownNormalizer
from rag_lab.models import NodeType
from rag_lab.parsing import MarkdownStructureParser

FIXTURE = Path(__file__).parent / "fixtures/golden.md"


def test_normalizer_preserves_code_and_normalizes_headings() -> None:
  source = "##Heading###\r\n\r\n\r\n```py\nx =  1\n```\n"
  normalized = MarkdownNormalizer().normalize(source)
  assert normalized.startswith("## Heading")
  assert "\n\n\n" not in normalized
  assert "x =  1" in normalized


def test_ast_has_offsets_heading_paths_and_special_blocks() -> None:
  markdown = FIXTURE.read_text(encoding="utf-8")
  document = MarkdownStructureParser().parse("golden", markdown)
  types = {block.node_type for block in document.blocks}
  assert {
    NodeType.HEADING,
    NodeType.PARAGRAPH,
    NodeType.LIST,
    NodeType.CODE_BLOCK,
    NodeType.TABLE,
    NodeType.QUOTE,
  } <= types
  paragraph = next(block for block in document.blocks if block.node_type == NodeType.PARAGRAPH)
  assert paragraph.heading_path == ["Redis", "Stream"]
  assert document.markdown[paragraph.start_offset:paragraph.end_offset].strip() == paragraph.text


def test_code_block_is_one_ast_block() -> None:
  document = MarkdownStructureParser().parse("golden", FIXTURE.read_text(encoding="utf-8"))
  code_blocks = [block for block in document.blocks if block.node_type == NodeType.CODE_BLOCK]
  assert len(code_blocks) == 1
  assert "acknowledge" in code_blocks[0].text

