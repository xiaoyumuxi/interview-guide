from __future__ import annotations

import re
import unicodedata


class MarkdownNormalizer:
  """Conservative structural cleanup. Facts and block contents are preserved."""

  _heading = re.compile(r"^(#{1,6})[ \t]*(.*)$")
  _blank_lines = re.compile(r"\n{3,}")

  def normalize(self, markdown: str) -> str:
    text = unicodedata.normalize("NFC", markdown).replace("\r\n", "\n").replace("\r", "\n")
    output: list[str] = []
    in_fence = False
    fence_marker = ""
    for original in text.split("\n"):
      line = original.rstrip()
      stripped = line.lstrip()
      if stripped.startswith(("```", "~~~")):
        marker = stripped[:3]
        if not in_fence:
          in_fence, fence_marker = True, marker
        elif marker == fence_marker:
          in_fence, fence_marker = False, ""
        output.append(line)
        continue
      if in_fence:
        output.append(original)
        continue
      match = self._heading.match(line)
      if match:
        title = match.group(2).strip().strip("#").strip()
        if title:
          output.append(f"{match.group(1)} {title}")
        continue
      output.append(line.expandtabs(2))
    normalized = "\n".join(output).strip() + "\n"
    return self._blank_lines.sub("\n\n", normalized)

