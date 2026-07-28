from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

IDENTITY_FIELDS = ("experiment_id", "dataset", "strategy", "group")
GROUPS = ("HARD_NEGATIVE", "NEGATIVE_BEARING")
CSV_FIELDS = [
  *IDENTITY_FIELDS,
  "query_count",
  "hard_negative_query_count",
  "negative_bearing_query_count",
  "gold_mapped_query_count",
  "negative_mapped_query_count",
  "margin_eligible_query_count",
  "pairwise_comparison_count",
  "pairwise_gold_win_count",
  "negative_exposure_at_1",
  "negative_exposure_at_3",
  "negative_exposure_at_5",
  "negative_exposure_at_10",
  "gold_before_negative_rate_at_5",
  "gold_before_negative_success_count_at_5",
  "gold_before_negative_query_count_at_5",
  "pairwise_gold_win_rate",
  "average_gold_negative_score_margin",
  "p50_gold_negative_score_margin",
  "minimum_gold_negative_score_margin",
]


def build_hard_negative_rows(reports: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
  rows: list[dict[str, Any]] = []
  for dataset_name, report in reports.items():
    for strategy, result in report["strategies"].items():
      for group in GROUPS:
        metrics = result["metrics"].get(group, {})
        rows.append({
          "experiment_id": report["experiment_id"],
          "dataset": dataset_name,
          "strategy": strategy,
          "group": group,
          "query_count": metrics.get("QueryCount", 0),
          "hard_negative_query_count": metrics.get("HardNegativeQueryCount", 0),
          "negative_bearing_query_count": metrics.get("NegativeBearingQueryCount", 0),
          "gold_mapped_query_count": metrics.get("GoldMappedQueryCount", 0),
          "negative_mapped_query_count": metrics.get("NegativeMappedQueryCount", 0),
          "margin_eligible_query_count": metrics.get("MarginEligibleQueryCount", 0),
          "pairwise_comparison_count": metrics.get("PairwiseComparisonCount", 0),
          "pairwise_gold_win_count": metrics.get("PairwiseGoldWinCount", 0),
          **{
            f"negative_exposure_at_{k}": metrics.get(f"NegativeExposure@{k}Query", "")
            for k in (1, 3, 5, 10)
          },
          "gold_before_negative_rate_at_5": metrics.get("GoldBeforeNegativeRate@5", ""),
          "gold_before_negative_success_count_at_5": metrics.get(
            "GoldBeforeNegativeSuccessCount@5", 0,
          ),
          "gold_before_negative_query_count_at_5": metrics.get(
            "GoldBeforeNegativeQueryCount@5", 0,
          ),
          "pairwise_gold_win_rate": metrics.get("PairwiseGoldWinRate", ""),
          "average_gold_negative_score_margin": metrics.get(
            "AverageGoldNegativeScoreMargin", "",
          ),
          "p50_gold_negative_score_margin": metrics.get("P50GoldNegativeScoreMargin", ""),
          "minimum_gold_negative_score_margin": metrics.get(
            "MinimumGoldNegativeScoreMargin", "",
          ),
        })
  return rows


def write_hard_negative_csv(rows: list[dict[str, Any]], output: Path) -> None:
  output.parent.mkdir(parents=True, exist_ok=True)
  with output.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
    writer.writeheader()
    writer.writerows(rows)
