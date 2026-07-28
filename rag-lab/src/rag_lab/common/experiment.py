from __future__ import annotations

import hashlib
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REQUIRED_EXPERIMENT_METADATA = {
  "experiment_id",
  "timestamp",
  "git_commit",
  "dataset_name",
  "dataset_sha256",
  "corpus_manifest_sha256",
  "embedding_model",
  "embedding_dimensions",
  "tokenizer_model",
  "token_count_mode",
  "python_version",
  "platform",
  "os_version",
  "machine",
  "device",
  "document_count",
  "query_count",
  "random_seed",
  "cloud_api_enabled",
  "test_executed",
}


def build_experiment_metadata(
  *,
  experiment_id: str,
  dataset_name: str,
  dataset_path: Path,
  corpus_manifest_path: Path,
  embedding_model: str,
  embedding_dimensions: int,
  tokenizer_model: str,
  token_count_mode: str,
  device: str,
  document_count: int,
  query_count: int,
  random_seed: int,
  cloud_api_enabled: bool,
  project_root: Path,
  timestamp: str | None = None,
  test_executed: bool = False,
) -> dict[str, Any]:
  metadata = {
    "experiment_id": experiment_id,
    "timestamp": timestamp or datetime.now(UTC).isoformat(),
    "git_commit": _git_commit(project_root),
    "dataset_name": dataset_name,
    "dataset_sha256": _sha256(dataset_path),
    "corpus_manifest_sha256": _sha256(corpus_manifest_path),
    "embedding_model": embedding_model,
    "embedding_dimensions": embedding_dimensions,
    "tokenizer_model": tokenizer_model,
    "token_count_mode": token_count_mode,
    "python_version": sys.version,
    "platform": platform.platform(),
    "os_version": platform.version(),
    "machine": platform.machine(),
    "device": device,
    "document_count": document_count,
    "query_count": query_count,
    "random_seed": random_seed,
    "cloud_api_enabled": cloud_api_enabled,
    "test_executed": test_executed,
  }
  missing = REQUIRED_EXPERIMENT_METADATA - metadata.keys()
  if missing:
    raise AssertionError(f"Missing experiment metadata: {sorted(missing)}")
  return metadata


def _sha256(path: Path) -> str:
  return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else "UNKNOWN"


def _git_commit(project_root: Path) -> str:
  try:
    return subprocess.check_output(
      ["git", "rev-parse", "HEAD"],
      cwd=project_root,
      text=True,
      stderr=subprocess.DEVNULL,
    ).strip()
  except (subprocess.CalledProcessError, FileNotFoundError):
    return "UNKNOWN"
