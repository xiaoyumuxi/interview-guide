#!/usr/bin/env python3
"""Closed-loop HTTP load generator for the virtual-thread LLM benchmark.

It uses only the Python standard library. Each worker owns one persistent HTTP/1.1
connection, so concurrency means the number of simultaneously outstanding
application requests. Formal runs use an exact request count per worker, making
the fixed and virtual groups comparable at the same concurrency and request count.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import gzip
import json
import math
import os
import statistics
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class HttpConnection:
    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter

    @classmethod
    async def open(cls, host: str, port: int) -> "HttpConnection":
        reader, writer = await asyncio.open_connection(host, port)
        return cls(reader, writer)

    async def close(self) -> None:
        self.writer.close()
        try:
            await self.writer.wait_closed()
        except (ConnectionError, BrokenPipeError):
            pass

    async def request(self, method: str, path: str) -> tuple[int, bytes]:
        request = (
            f"{method} {path} HTTP/1.1\r\n"
            "Host: 127.0.0.1\r\n"
            "Accept: application/json\r\n"
            "Content-Length: 0\r\n"
            "Connection: keep-alive\r\n"
            "\r\n"
        )
        self.writer.write(request.encode("ascii"))
        await self.writer.drain()
        return await read_response(self.reader)


async def read_response(reader: asyncio.StreamReader) -> tuple[int, bytes]:
    status_line = await reader.readline()
    if not status_line:
        raise ConnectionError("server closed connection before status line")
    parts = status_line.decode("iso-8859-1").strip().split(" ", 2)
    if len(parts) < 2:
        raise ConnectionError(f"invalid HTTP status line: {status_line!r}")
    status = int(parts[1])
    headers: dict[str, str] = {}
    while True:
        line = await reader.readline()
        if line in (b"\r\n", b"\n", b""):
            break
        name, value = line.decode("iso-8859-1").split(":", 1)
        headers[name.strip().lower()] = value.strip().lower()

    if "content-length" in headers:
        body = await reader.readexactly(int(headers["content-length"]))
    elif headers.get("transfer-encoding") == "chunked":
        chunks: list[bytes] = []
        while True:
            size_line = await reader.readline()
            size = int(size_line.split(b";", 1)[0].strip(), 16)
            if size == 0:
                await reader.readline()
                break
            chunks.append(await reader.readexactly(size))
            await reader.readexactly(2)
        body = b"".join(chunks)
    else:
        body = b""
    return status, body


async def one_json_request(
    host: str,
    port: int,
    method: str,
    path: str,
) -> dict[str, Any]:
    connection = await HttpConnection.open(host, port)
    try:
        status, body = await connection.request(method, path)
        if status != 200:
            raise RuntimeError(f"{method} {path} returned HTTP {status}: {body[:200]!r}")
        return json.loads(body)
    finally:
        await connection.close()


async def warmup_worker(host: str, port: int, deadline: float) -> None:
    connection: HttpConnection | None = None
    try:
        while time.monotonic() < deadline:
            try:
                if connection is None:
                    connection = await HttpConnection.open(host, port)
                await asyncio.wait_for(
                    connection.request("POST", "/benchmark/llm"),
                    timeout=180,
                )
            except (OSError, ConnectionError, asyncio.TimeoutError):
                if connection is not None:
                    await connection.close()
                connection = None
    finally:
        if connection is not None:
            await connection.close()


async def warmup(host: str, port: int, concurrency: int, seconds: int) -> None:
    deadline = time.monotonic() + seconds
    await asyncio.gather(
        *(warmup_worker(host, port, deadline) for _ in range(concurrency))
    )


async def measurement_worker(
    worker_id: int,
    host: str,
    port: int,
    request_count: int,
    rows: list[dict[str, Any]],
) -> None:
    connection: HttpConnection | None = None
    try:
        for sequence in range(request_count):
            started = time.perf_counter_ns()
            status = 0
            queue_wait_ms: float | None = None
            execution_ms: float | None = None
            virtual_thread: bool | None = None
            error = ""
            try:
                if connection is None:
                    connection = await HttpConnection.open(host, port)
                status, body = await asyncio.wait_for(
                    connection.request("POST", "/benchmark/llm"),
                    timeout=180,
                )
                payload = json.loads(body)
                if status == 200:
                    queue_wait_ms = float(payload["queueWaitMs"])
                    execution_ms = float(payload["executionMs"])
                    virtual_thread = bool(payload["virtualThread"])
                else:
                    error = body.decode("utf-8", errors="replace")[:300]
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
                if connection is not None:
                    await connection.close()
                connection = None
            finished = time.perf_counter_ns()
            rows.append(
                {
                    "worker": worker_id,
                    "sequence": sequence,
                    "status": status,
                    "end_to_end_ms": (finished - started) / 1_000_000.0,
                    "queue_wait_ms": queue_wait_ms,
                    "execution_ms": execution_ms,
                    "virtual_thread": virtual_thread,
                    "error": error,
                }
            )
    finally:
        if connection is not None:
            await connection.close()


async def process_rss_kib(pid: int) -> int | None:
    try:
        process = await asyncio.create_subprocess_exec(
            "ps",
            "-o",
            "rss=",
            "-p",
            str(pid),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, _ = await process.communicate()
        if process.returncode != 0:
            return None
        value = stdout.decode().strip()
        return int(value) if value else None
    except (OSError, ValueError):
        return None


async def capture_thread_dump(jcmd: str, pid: int, output_path: Path) -> None:
    try:
        process = await asyncio.create_subprocess_exec(
            jcmd,
            str(pid),
            "Thread.print",
            "-l",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        stdout, _ = await process.communicate()
        output_path.write_bytes(stdout)
    except OSError as exc:
        output_path.write_text(f"thread dump failed: {exc}\n", encoding="utf-8")


async def sample_state(
    args: argparse.Namespace,
    stop_event: asyncio.Event,
    started_at: float,
    samples: list[dict[str, Any]],
    thread_dump_path: Path,
) -> None:
    dumped = False
    while not stop_event.is_set():
        try:
            state = await one_json_request(args.host, args.port, "GET", "/benchmark/state")
            rss_kib = await process_rss_kib(args.server_pid) if args.server_pid else None
            state["sampleElapsedSeconds"] = time.monotonic() - started_at
            state["rssKiB"] = rss_kib
            samples.append(state)
        except Exception as exc:
            samples.append({"sampleError": f"{type(exc).__name__}: {exc}"})

        elapsed = time.monotonic() - started_at
        if (
            not dumped
            and elapsed >= args.thread_dump_after
            and args.server_pid
            and args.jcmd
        ):
            dumped = True
            await capture_thread_dump(args.jcmd, args.server_pid, thread_dump_path)
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=args.sample_interval)
        except asyncio.TimeoutError:
            pass


async def progress_reporter(
    stop_event: asyncio.Event,
    rows: list[dict[str, Any]],
    total: int,
    started_at: float,
) -> None:
    while not stop_event.is_set():
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=30)
        except asyncio.TimeoutError:
            elapsed = time.monotonic() - started_at
            print(
                f"measurement progress: {len(rows)}/{total} responses, "
                f"elapsed={elapsed:.1f}s",
                flush=True,
            )


def percentile(values: list[float], quantile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, math.ceil(quantile * len(ordered)) - 1)
    return ordered[index]


def max_number(samples: list[dict[str, Any]], field: str) -> float | int | None:
    values = [
        sample[field]
        for sample in samples
        if isinstance(sample.get(field), (int, float))
    ]
    return max(values) if values else None


def mean_number(samples: list[dict[str, Any]], field: str) -> float | None:
    values = [
        float(sample[field])
        for sample in samples
        if isinstance(sample.get(field), (int, float)) and sample[field] >= 0
    ]
    return statistics.fmean(values) if values else None


def latency_summary(values: list[float]) -> dict[str, float | None]:
    return {
        "p50Ms": percentile(values, 0.50),
        "p90Ms": percentile(values, 0.90),
        "p95Ms": percentile(values, 0.95),
        "p99Ms": percentile(values, 0.99),
        "maxMs": max(values) if values else None,
    }


def write_raw_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


async def run(args: argparse.Namespace) -> None:
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = f"{args.mode}-c{args.concurrency}-r{args.repeat}"
    raw_path = output_dir / "raw" / f"{prefix}.csv.gz"
    summary_path = output_dir / f"summary-{prefix}.json"
    samples_path = output_dir / "samples" / f"{prefix}.json"
    thread_dump_path = output_dir / "thread-dumps" / f"{prefix}.txt"
    samples_path.parent.mkdir(parents=True, exist_ok=True)
    thread_dump_path.parent.mkdir(parents=True, exist_ok=True)

    print(
        f"warmup: mode={args.mode}, concurrency={args.concurrency}, "
        f"duration={args.warmup_seconds}s",
        flush=True,
    )
    await one_json_request(args.host, args.port, "POST", "/benchmark/state/reset")
    await warmup(args.host, args.port, args.concurrency, args.warmup_seconds)
    await one_json_request(args.host, args.port, "POST", "/benchmark/state/reset")

    rows: list[dict[str, Any]] = []
    samples: list[dict[str, Any]] = []
    stop_event = asyncio.Event()
    total_requests = args.concurrency * args.requests_per_worker
    started_at = time.monotonic()
    started_wall = datetime.now(timezone.utc).isoformat()
    sampler = asyncio.create_task(
        sample_state(args, stop_event, started_at, samples, thread_dump_path)
    )
    progress = asyncio.create_task(
        progress_reporter(stop_event, rows, total_requests, started_at)
    )
    workers = [
        asyncio.create_task(
            measurement_worker(
                worker_id,
                args.host,
                args.port,
                args.requests_per_worker,
                rows,
            )
        )
        for worker_id in range(args.concurrency)
    ]
    await asyncio.gather(*workers)
    duration_seconds = time.monotonic() - started_at
    stop_event.set()
    await asyncio.gather(sampler, progress)

    successful_rows = [
        row for row in rows if row["status"] == 200 and not row["error"]
    ]
    end_to_end = [float(row["end_to_end_ms"]) for row in successful_rows]
    queue_wait = [
        float(row["queue_wait_ms"])
        for row in successful_rows
        if row["queue_wait_ms"] is not None
    ]
    execution = [
        float(row["execution_ms"])
        for row in successful_rows
        if row["execution_ms"] is not None
    ]
    final_state = await one_json_request(
        args.host, args.port, "GET", "/benchmark/state"
    )
    samples.append(final_state)
    cpu_load = mean_number(samples, "processCpuLoad")
    rss_max_kib = max_number(samples, "rssKiB")
    summary = {
        "mode": args.mode,
        "concurrency": args.concurrency,
        "repeat": args.repeat,
        "startedAtUtc": started_wall,
        "warmupSeconds": args.warmup_seconds,
        "requestsPerWorker": args.requests_per_worker,
        "totalRequests": len(rows),
        "successfulRequests": len(successful_rows),
        "failedRequests": len(rows) - len(successful_rows),
        "durationSeconds": duration_seconds,
        "throughputRequestsPerSecond": len(rows) / duration_seconds,
        "errorRatePercent": (
            100.0 * (len(rows) - len(successful_rows)) / len(rows)
            if rows
            else None
        ),
        "endToEndLatency": latency_summary(end_to_end),
        "queueWait": latency_summary(queue_wait),
        "execution": latency_summary(execution),
        "peakPlatformThreads": max_number(samples, "peakPlatformThreads"),
        "maxLivePlatformThreads": max_number(samples, "livePlatformThreads"),
        "peakVirtualExecutorTasks": max_number(samples, "peakVirtualExecutorTasks"),
        "maxFixedActiveThreads": max_number(samples, "activeExecutorTasks"),
        "maxFixedPoolSize": max_number(samples, "executorPoolSize"),
        "maxExecutorQueueSize": max_number(samples, "executorQueueSize"),
        "averageProcessCpuPercent": cpu_load * 100.0 if cpu_load is not None else None,
        "maxHeapUsedMiB": (
            max_number(samples, "heapUsedBytes") / 1024.0 / 1024.0
            if max_number(samples, "heapUsedBytes") is not None
            else None
        ),
        "maxRssMiB": (
            float(rss_max_kib) / 1024.0 if rss_max_kib is not None else None
        ),
        "finalState": final_state,
    }
    write_raw_rows(raw_path, rows)
    samples_path.write_text(
        json.dumps(samples, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=18080)
    parser.add_argument("--mode", choices=("fixed", "virtual"), required=True)
    parser.add_argument("--concurrency", type=int, required=True)
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--warmup-seconds", type=int, default=30)
    parser.add_argument("--requests-per-worker", type=int, default=40)
    parser.add_argument("--sample-interval", type=float, default=0.25)
    parser.add_argument("--server-pid", type=int)
    parser.add_argument("--jcmd")
    parser.add_argument("--thread-dump-after", type=float, default=10.0)
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args()


if __name__ == "__main__":
    asyncio.run(run(parse_args()))
