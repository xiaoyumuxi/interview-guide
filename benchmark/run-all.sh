#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_ID="${BENCHMARK_RUN_ID:-$(date +%Y%m%d-%H%M%S)}"
RESULT_DIR="${BENCHMARK_RESULT_DIR:-$SCRIPT_DIR/results/$RUN_ID}"

export BENCHMARK_RUN_ID="$RUN_ID"
export BENCHMARK_RESULT_DIR="$RESULT_DIR"

"$SCRIPT_DIR/run-mode.sh" fixed
"$SCRIPT_DIR/run-mode.sh" virtual
python3 "$SCRIPT_DIR/analyze.py" "$RESULT_DIR"

echo "all benchmark groups completed: $RESULT_DIR"
