#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]] || [[ "$1" != "fixed" && "$1" != "virtual" ]]; then
  echo "usage: $0 fixed|virtual" >&2
  exit 2
fi

MODE="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
RUN_ID="${BENCHMARK_RUN_ID:-$(date +%Y%m%d-%H%M%S)}"
RESULT_DIR="${BENCHMARK_RESULT_DIR:-$SCRIPT_DIR/results/$RUN_ID}"
CONCURRENCIES="${BENCHMARK_CONCURRENCIES:-10 50 100 200 500}"
REPEATS="${BENCHMARK_REPEATS:-3}"
WARMUP_SECONDS="${BENCHMARK_WARMUP_SECONDS:-30}"
REQUESTS_PER_WORKER="${BENCHMARK_REQUESTS_PER_WORKER:-40}"
CLIENT_PORT="${BENCHMARK_CLIENT_PORT:-18080}"
MOCK_PORT="${BENCHMARK_MOCK_PORT:-18081}"
FIXED_POOL_SIZE="${BENCHMARK_FIXED_POOL_SIZE:-32}"
JVM_ARGS=(
  -Xms512m
  -Xmx512m
  -XX:+UseG1GC
  -Djdk.tracePinnedThreads=full
)

mkdir -p "$RESULT_DIR/logs" "$RESULT_DIR/jfr"

export JAVA_HOME="${BENCHMARK_GRADLE_JAVA_HOME:-/Library/Java/JavaVirtualMachines/jdk-21.jdk/Contents/Home}"
"$ROOT_DIR/gradlew" :benchmark:bootJar --no-daemon

if [[ -n "${BENCHMARK_JAVA_HOME:-}" ]]; then
  JAVA_25_HOME="$BENCHMARK_JAVA_HOME"
else
  JAVA_25_HOME="$("$ROOT_DIR/gradlew" -q :benchmark:printJavaToolchainHome)"
fi
JAVA_BIN="$JAVA_25_HOME/bin/java"
JCMD_BIN="$JAVA_25_HOME/bin/jcmd"
JFR_BIN="$JAVA_25_HOME/bin/jfr"
JAR_PATH="$ROOT_DIR/benchmark/build/libs/benchmark-0.0.1-SNAPSHOT.jar"

MOCK_PID=""
CLIENT_PID=""

cleanup() {
  if [[ -n "$CLIENT_PID" ]] && kill -0 "$CLIENT_PID" 2>/dev/null; then
    kill "$CLIENT_PID" 2>/dev/null || true
    wait "$CLIENT_PID" 2>/dev/null || true
  fi
  if [[ -n "$MOCK_PID" ]] && kill -0 "$MOCK_PID" 2>/dev/null; then
    kill "$MOCK_PID" 2>/dev/null || true
    wait "$MOCK_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

wait_for_health() {
  local port="$1"
  local process_pid="$2"
  local label="$3"
  for _ in $(seq 1 90); do
    if ! kill -0 "$process_pid" 2>/dev/null; then
      echo "$label process exited before becoming healthy" >&2
      return 1
    fi
    if curl -fsS "http://127.0.0.1:${port}/actuator/health" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  echo "$label did not become healthy within 90 seconds" >&2
  return 1
}

"$JAVA_BIN" -Xms256m -Xmx256m -XX:+UseG1GC \
  -jar "$JAR_PATH" \
  --server.port="$MOCK_PORT" \
  --benchmark.client.enabled=false \
  --benchmark.mock.enabled=true \
  --benchmark.mock.delay=1500ms \
  >"$RESULT_DIR/logs/mock-${MODE}.log" 2>&1 &
MOCK_PID="$!"
wait_for_health "$MOCK_PORT" "$MOCK_PID" "mock"

"$JAVA_BIN" "${JVM_ARGS[@]}" \
  -jar "$JAR_PATH" \
  --server.port="$CLIENT_PORT" \
  --benchmark.client.enabled=true \
  --benchmark.mock.enabled=false \
  --benchmark.mock.base-url="http://127.0.0.1:${MOCK_PORT}/v1" \
  --llm.executor.type="$MODE" \
  --llm.executor.fixed-pool-size="$FIXED_POOL_SIZE" \
  >"$RESULT_DIR/logs/client-${MODE}.log" 2>&1 &
CLIENT_PID="$!"
wait_for_health "$CLIENT_PORT" "$CLIENT_PID" "client"

{
  date -u +"timestamp_utc=%Y-%m-%dT%H:%M:%SZ"
  uname -a
  "$JAVA_BIN" -version
  echo "java_home=$JAVA_25_HOME"
  echo "jvm_args=${JVM_ARGS[*]}"
  echo "mode=$MODE"
  echo "fixed_pool_size=$FIXED_POOL_SIZE"
  echo "mock_delay_ms=1500"
  echo "concurrencies=$CONCURRENCIES"
  echo "repeats=$REPEATS"
  echo "warmup_seconds=$WARMUP_SECONDS"
  echo "requests_per_worker=$REQUESTS_PER_WORKER"
  sysctl -n machdep.cpu.brand_string 2>/dev/null || true
  sysctl -n hw.physicalcpu 2>/dev/null || true
  sysctl -n hw.logicalcpu 2>/dev/null || true
  sysctl -n hw.memsize 2>/dev/null || true
} >"$RESULT_DIR/environment-${MODE}.txt" 2>&1

JFR_NAME="llmBenchmark${MODE}"
"$JCMD_BIN" "$CLIENT_PID" JFR.start \
  name="$JFR_NAME" settings=profile maxsize=256m >/dev/null

for repeat in $(seq 1 "$REPEATS"); do
  for concurrency in $CONCURRENCIES; do
    echo "running mode=$MODE concurrency=$concurrency repeat=$repeat" | tee -a \
      "$RESULT_DIR/run.log"
    python3 "$SCRIPT_DIR/load.py" \
      --host 127.0.0.1 \
      --port "$CLIENT_PORT" \
      --mode "$MODE" \
      --concurrency "$concurrency" \
      --repeat "$repeat" \
      --warmup-seconds "$WARMUP_SECONDS" \
      --requests-per-worker "$REQUESTS_PER_WORKER" \
      --server-pid "$CLIENT_PID" \
      --jcmd "$JCMD_BIN" \
      --output-dir "$RESULT_DIR"
  done
done

"$JCMD_BIN" "$CLIENT_PID" JFR.dump \
  name="$JFR_NAME" filename="$RESULT_DIR/jfr/${MODE}.jfr" >/dev/null
"$JCMD_BIN" "$CLIENT_PID" JFR.stop name="$JFR_NAME" >/dev/null
"$JFR_BIN" summary "$RESULT_DIR/jfr/${MODE}.jfr" \
  >"$RESULT_DIR/jfr/${MODE}-summary.txt"
"$JFR_BIN" print --events jdk.VirtualThreadPinned "$RESULT_DIR/jfr/${MODE}.jfr" \
  >"$RESULT_DIR/jfr/${MODE}-pinned.txt"

python3 "$SCRIPT_DIR/analyze.py" "$RESULT_DIR"
echo "completed mode=$MODE results=$RESULT_DIR"
