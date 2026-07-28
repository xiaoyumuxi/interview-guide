from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_config(path: Path) -> dict[str, Any]:
  with path.open(encoding="utf-8") as handle:
    config = yaml.safe_load(handle) or {}
  if config.get("cloud", {}).get("enabled", False):
    raise ValueError("Cloud providers are not implemented in Phase 1")
  return config

