from pathlib import Path

import pytest

from rag_lab.evaluation.runner import BenchmarkRunner


def test_no_test_execution() -> None:
  runner = BenchmarkRunner(
    {
      "dataset": {
        "path": "data/datasets/java-interview-real-v1/test-agent-reviewed.jsonl",
        "version": "java-interview-real-v1-test-agent-reviewed",
      },
    },
    Path("."),
  )
  with pytest.raises(ValueError, match="NOT EXECUTED"):
    runner._assert_not_test_dataset()
