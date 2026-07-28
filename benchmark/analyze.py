#!/usr/bin/env python3
"""Aggregate benchmark summaries and render dependency-free SVG charts."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable


def nested(record: dict[str, Any], path: str) -> float | None:
    value: Any = record
    for key in path.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return float(value) if isinstance(value, (int, float)) else None


def median(records: list[dict[str, Any]], path: str) -> float | None:
    values = [value for record in records if (value := nested(record, path)) is not None]
    return statistics.median(values) if values else None


def fmt(value: float | None, digits: int = 2) -> str:
    return "未测得" if value is None else f"{value:.{digits}f}"


def improvement(virtual: float | None, fixed: float | None, higher_is_better: bool) -> float | None:
    if virtual is None or fixed is None or fixed == 0:
        return None
    if higher_is_better:
        return (virtual - fixed) / fixed * 100.0
    return (fixed - virtual) / fixed * 100.0


def xml_escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render_chart(
    path: Path,
    title: str,
    y_label: str,
    concurrencies: list[int],
    series: dict[str, list[float | None]],
) -> None:
    width, height = 900, 520
    left, right, top, bottom = 92, 36, 58, 72
    plot_width = width - left - right
    plot_height = height - top - bottom
    values = [value for points in series.values() for value in points if value is not None]
    y_max = max(values) * 1.12 if values else 1.0
    if y_max <= 0:
        y_max = 1.0
    colors = {"Fixed-32": "#dc2626", "Virtual": "#2563eb"}

    def x(index: int) -> float:
        return left + (plot_width * index / max(1, len(concurrencies) - 1))

    def y(value: float) -> float:
        return top + plot_height - (value / y_max * plot_height)

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{width / 2}" y="30" text-anchor="middle" '
        f'font-family="system-ui,sans-serif" font-size="20" font-weight="600">'
        f'{xml_escape(title)}</text>',
    ]
    for tick in range(6):
        value = y_max * tick / 5
        y_pos = y(value)
        lines.append(
            f'<line x1="{left}" y1="{y_pos:.1f}" x2="{width - right}" y2="{y_pos:.1f}" '
            'stroke="#e5e7eb" stroke-width="1"/>'
        )
        lines.append(
            f'<text x="{left - 10}" y="{y_pos + 4:.1f}" text-anchor="end" '
            f'font-family="system-ui,sans-serif" font-size="12" fill="#4b5563">{value:.1f}</text>'
        )
    lines.extend(
        [
            f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}" '
            'stroke="#111827" stroke-width="1.5"/>',
            f'<line x1="{left}" y1="{top + plot_height}" x2="{width - right}" '
            f'y2="{top + plot_height}" stroke="#111827" stroke-width="1.5"/>',
        ]
    )
    for index, concurrency in enumerate(concurrencies):
        x_pos = x(index)
        lines.append(
            f'<text x="{x_pos:.1f}" y="{top + plot_height + 25}" text-anchor="middle" '
            f'font-family="system-ui,sans-serif" font-size="12">{concurrency}</text>'
        )
    lines.append(
        f'<text x="{left + plot_width / 2}" y="{height - 20}" text-anchor="middle" '
        'font-family="system-ui,sans-serif" font-size="14">Concurrency</text>'
    )
    lines.append(
        f'<text x="22" y="{top + plot_height / 2}" text-anchor="middle" '
        f'transform="rotate(-90 22 {top + plot_height / 2})" '
        f'font-family="system-ui,sans-serif" font-size="14">{xml_escape(y_label)}</text>'
    )

    for name, points in series.items():
        color = colors[name]
        coordinates = [
            f"{x(index):.1f},{y(value):.1f}"
            for index, value in enumerate(points)
            if value is not None
        ]
        if coordinates:
            lines.append(
                f'<polyline points="{" ".join(coordinates)}" fill="none" '
                f'stroke="{color}" stroke-width="3"/>'
            )
        for index, value in enumerate(points):
            if value is not None:
                lines.append(
                    f'<circle cx="{x(index):.1f}" cy="{y(value):.1f}" r="4.5" '
                    f'fill="{color}"><title>{xml_escape(name)} C={concurrencies[index]}: '
                    f'{value:.3f}</title></circle>'
                )

    legend_x = width - right - 190
    for index, name in enumerate(("Fixed-32", "Virtual")):
        y_pos = top + 16 + index * 24
        lines.append(
            f'<line x1="{legend_x}" y1="{y_pos}" x2="{legend_x + 28}" y2="{y_pos}" '
            f'stroke="{colors[name]}" stroke-width="3"/>'
        )
        lines.append(
            f'<text x="{legend_x + 36}" y="{y_pos + 4}" '
            f'font-family="system-ui,sans-serif" font-size="13">{name}</text>'
        )
    lines.append("</svg>")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> None:
    result_dir = Path(args.result_dir).resolve()
    summaries = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(result_dir.glob("summary-*.json"))
    ]
    if not summaries:
        raise SystemExit(f"no summary JSON files found in {result_dir}")

    grouped: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for summary in summaries:
        grouped[(summary["mode"], int(summary["concurrency"]))].append(summary)

    fields = {
        "throughput_rps": "throughputRequestsPerSecond",
        "p50_ms": "endToEndLatency.p50Ms",
        "p90_ms": "endToEndLatency.p90Ms",
        "p95_ms": "endToEndLatency.p95Ms",
        "p99_ms": "endToEndLatency.p99Ms",
        "max_ms": "endToEndLatency.maxMs",
        "queue_wait_p95_ms": "queueWait.p95Ms",
        "execution_p95_ms": "execution.p95Ms",
        "peak_platform_threads": "peakPlatformThreads",
        "peak_virtual_tasks": "peakVirtualExecutorTasks",
        "peak_executor_tasks": "maxFixedActiveThreads",
        "max_executor_queue": "maxExecutorQueueSize",
        "cpu_percent": "averageProcessCpuPercent",
        "heap_mib": "maxHeapUsedMiB",
        "rss_mib": "maxRssMiB",
        "error_rate_percent": "errorRatePercent",
        "duration_seconds": "durationSeconds",
        "total_requests": "totalRequests",
    }
    aggregate_rows: list[dict[str, Any]] = []
    for (mode, concurrency), records in sorted(
        grouped.items(), key=lambda item: (item[0][1], item[0][0])
    ):
        row: dict[str, Any] = {
            "mode": "Fixed-32" if mode == "fixed" else "Virtual",
            "concurrency": concurrency,
            "repeats": len(records),
        }
        for output_name, input_path in fields.items():
            row[output_name] = median(records, input_path)
        aggregate_rows.append(row)

    with (result_dir / "summary.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(aggregate_rows[0].keys()))
        writer.writeheader()
        writer.writerows(aggregate_rows)

    row_by_key = {
        (row["mode"], int(row["concurrency"])): row for row in aggregate_rows
    }
    concurrencies = sorted({int(row["concurrency"]) for row in aggregate_rows})
    comparison_rows: list[dict[str, Any]] = []
    for concurrency in concurrencies:
        fixed = row_by_key.get(("Fixed-32", concurrency))
        virtual = row_by_key.get(("Virtual", concurrency))
        if fixed is None or virtual is None:
            continue
        comparison_rows.append(
            {
                "concurrency": concurrency,
                "throughput_improvement_percent": improvement(
                    virtual["throughput_rps"], fixed["throughput_rps"], True
                ),
                "p95_reduction_percent": improvement(
                    virtual["p95_ms"], fixed["p95_ms"], False
                ),
                "platform_thread_reduction_percent": improvement(
                    virtual["peak_platform_threads"],
                    fixed["peak_platform_threads"],
                    False,
                ),
                "queue_wait_reduction_percent": improvement(
                    virtual["queue_wait_p95_ms"],
                    fixed["queue_wait_p95_ms"],
                    False,
                ),
            }
        )
    if comparison_rows:
        with (result_dir / "comparison.csv").open(
            "w", encoding="utf-8", newline=""
        ) as handle:
            writer = csv.DictWriter(
                handle, fieldnames=list(comparison_rows[0].keys())
            )
            writer.writeheader()
            writer.writerows(comparison_rows)

    charts = result_dir / "charts"
    charts.mkdir(exist_ok=True)

    def chart_series(field: str) -> dict[str, list[float | None]]:
        return {
            mode: [
                row_by_key.get((mode, concurrency), {}).get(field)
                for concurrency in concurrencies
            ]
            for mode in ("Fixed-32", "Virtual")
        }

    chart_specs: list[tuple[str, str, str, str]] = [
        ("throughput.svg", "Concurrency vs Throughput", "Requests / second", "throughput_rps"),
        ("p95-latency.svg", "Concurrency vs P95 Latency", "P95 latency (ms)", "p95_ms"),
        ("p99-latency.svg", "Concurrency vs P99 Latency", "P99 latency (ms)", "p99_ms"),
        (
            "platform-threads.svg",
            "Concurrency vs Peak Platform Threads",
            "Peak platform threads",
            "peak_platform_threads",
        ),
        (
            "queue-wait-p95.svg",
            "Concurrency vs Queue Wait P95",
            "Queue wait P95 (ms)",
            "queue_wait_p95_ms",
        ),
    ]
    for filename, title, y_label, field in chart_specs:
        render_chart(
            charts / filename,
            title,
            y_label,
            concurrencies,
            chart_series(field),
        )
    print(f"wrote {result_dir / 'summary.csv'}")
    print(f"wrote {result_dir / 'comparison.csv'}")
    print(f"wrote {charts}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("result_dir")
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
