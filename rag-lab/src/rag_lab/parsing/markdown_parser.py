from __future__ import annotations

from markdown_it import MarkdownIt
from markdown_it.token import Token

from rag_lab.common.text import stable_id
from rag_lab.models import DocumentNode, NodeType, StructuredDocument


class MarkdownStructureParser:
  """Parse Markdown with markdown-it and project tokens into offset-aware blocks."""

  def __init__(self) -> None:
    self._parser = MarkdownIt("commonmark", {"html": True}).enable("table")

  def parse(self, document_id: str, markdown: str, source_path: str = "") -> StructuredDocument:
    tokens = self._parser.parse(markdown)
    line_offsets = self._line_offsets(markdown)
    headings: list[str] = []
    blocks: list[DocumentNode] = []
    index = 0
    while index < len(tokens):
      token = tokens[index]
      if token.type == "heading_open":
        inline = tokens[index + 1]
        level = int(token.tag[1])
        title = inline.content.strip()
        headings = headings[: level - 1]
        headings.append(title)
        blocks.append(self._node(document_id, NodeType.HEADING, token, markdown, line_offsets,
                                 headings.copy(), level, title))
        index += 3
        continue
      node_type = self._block_type(token)
      if node_type is not None and token.map:
        end_index = self._matching_block_end(tokens, index)
        blocks.append(self._node(document_id, node_type, token, markdown, line_offsets,
                                 headings.copy(), None))
        index = max(index + 1, end_index)
        continue
      index += 1
    root = DocumentNode(
      id=stable_id("node", document_id, "root"),
      node_type=NodeType.DOCUMENT,
      text=markdown,
      heading_level=None,
      heading_path=[],
      start_offset=0,
      end_offset=len(markdown),
      children=blocks,
    )
    return StructuredDocument(document_id, markdown, root, source_path)

  @staticmethod
  def _line_offsets(markdown: str) -> list[int]:
    offsets = [0]
    for index, char in enumerate(markdown):
      if char == "\n":
        offsets.append(index + 1)
    offsets.append(len(markdown))
    return offsets

  @staticmethod
  def _block_type(token: Token) -> NodeType | None:
    return {
      "paragraph_open": NodeType.PARAGRAPH,
      "bullet_list_open": NodeType.LIST,
      "ordered_list_open": NodeType.LIST,
      "fence": NodeType.CODE_BLOCK,
      "code_block": NodeType.CODE_BLOCK,
      "blockquote_open": NodeType.QUOTE,
      "table_open": NodeType.TABLE,
      "html_block": NodeType.TABLE if "<table" in token.content.lower() else NodeType.PARAGRAPH,
    }.get(token.type)

  @staticmethod
  def _matching_block_end(tokens: list[Token], start: int) -> int:
    token = tokens[start]
    if token.nesting != 1:
      return start + 1
    level = 1
    for index in range(start + 1, len(tokens)):
      if tokens[index].type == token.type:
        level += 1
      if tokens[index].type == token.type.replace("_open", "_close"):
        level -= 1
        if level == 0:
          return index + 1
    return start + 1

  @staticmethod
  def _node(
    document_id: str,
    node_type: NodeType,
    token: Token,
    markdown: str,
    offsets: list[int],
    heading_path: list[str],
    heading_level: int | None,
    text_override: str | None = None,
  ) -> DocumentNode:
    assert token.map is not None
    start_line, end_line = token.map
    start = offsets[min(start_line, len(offsets) - 1)]
    end = offsets[min(end_line, len(offsets) - 1)]
    text = text_override if text_override is not None else markdown[start:end].strip()
    return DocumentNode(
      id=stable_id("node", document_id, start, end, node_type),
      node_type=node_type,
      text=text,
      heading_level=heading_level,
      heading_path=heading_path,
      start_offset=start,
      end_offset=end,
      metadata={"source_map": [start_line, end_line]},
    )
