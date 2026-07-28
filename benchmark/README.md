# Virtual-thread LLM benchmark

This module is an isolated, reproducible benchmark for the blocking Spring AI
call path:

```text
HTTP client
  -> Spring MVC controller
  -> benchmark service
  -> fixed or virtual executor
  -> Spring AI ChatClient.prompt().call()
  -> OpenAI-compatible HTTP endpoint
  -> 1500 ms mock wait
  -> JSON serialization/deserialization
```

The mock endpoint runs in a separate JVM, so its threads and memory do not
contaminate the measured client JVM. Both modes use the same prompt, Spring AI
client, HTTP implementation, mock process, JVM flags, heap size, request count,
and concurrency. The only client-side difference is `llm.executor.type`.

Run the full specified matrix:

```bash
benchmark/run-all.sh
```

Defaults:

- modes: fixed pool of 32 and virtual thread per task
- concurrency: 10, 50, 100, 200, 500
- warmup: 30 seconds for every scenario
- formal requests: exactly 40 per worker (`40 * concurrency`)
- repeats: 3, aggregated by median
- mock delay: 1500 ms

At 1500 ms per request, 40 requests per worker makes an unconstrained group run
for at least 60 seconds. The fixed group takes longer once its 32 workers
saturate; this is intentional so both modes still execute the exact same number
of requests.

For a shorter diagnostic run:

```bash
BENCHMARK_CONCURRENCIES="10 50" \
BENCHMARK_REPEATS=1 \
BENCHMARK_WARMUP_SECONDS=5 \
BENCHMARK_REQUESTS_PER_WORKER=4 \
benchmark/run-all.sh
```

Every run gets a timestamped directory under `benchmark/results/` containing:

- per-request raw CSV data compressed with gzip;
- per-scenario JVM/process samples and JSON summaries;
- fixed/virtual thread dumps;
- JFR recordings and virtual-thread pinning event extracts;
- aggregate CSV comparisons and five SVG charts.
