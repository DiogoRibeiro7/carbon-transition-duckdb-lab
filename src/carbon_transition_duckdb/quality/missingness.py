"""Missingness reports by country and by metric.

Data completeness is part of the transition story: a falling score can reflect a
genuine transition *or* simply missing data. These helpers quantify how complete
each metric and each country is so that gaps are visible, not silent.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import cast

import pandas as pd

METRIC_COLUMNS: tuple[str, ...] = (
    "co2",
    "co2_per_capita",
    "primary_energy_consumption",
    "carbon_intensity",
    "fossil_share_energy",
    "renewables_share_energy",
    "renewables_share_elec",
    "electricity_generation",
)


def _present_metrics(frame: pd.DataFrame, metrics: Sequence[str]) -> list[str]:
    """Return the requested metrics that actually exist in the frame."""
    return [metric for metric in metrics if metric in frame.columns]


def missingness_by_metric(
    frame: pd.DataFrame, metrics: Sequence[str] = METRIC_COLUMNS
) -> pd.DataFrame:
    """Count missing values per metric across all rows.

    Returns one row per metric with ``n_total``, ``n_missing`` and
    ``pct_missing``, sorted by the most incomplete metric first.
    """
    columns = _present_metrics(frame, metrics)
    n_total = len(frame)
    records = []
    for metric in columns:
        n_missing = int(frame[metric].isna().sum())
        records.append(
            {
                "metric": metric,
                "n_total": n_total,
                "n_missing": n_missing,
                "pct_missing": round(100.0 * n_missing / n_total, 2) if n_total else 0.0,
            }
        )
    out = pd.DataFrame.from_records(
        records, columns=["metric", "n_total", "n_missing", "pct_missing"]
    )
    out = out.sort_values("pct_missing", ascending=False).reset_index(drop=True)
    return cast(pd.DataFrame, out)


def missingness_by_country(
    frame: pd.DataFrame,
    metrics: Sequence[str] = METRIC_COLUMNS,
    country_col: str = "country",
) -> pd.DataFrame:
    """Count missing metric cells per country.

    Returns one row per country with the number of rows, total metric cells,
    missing cells and the resulting missing percentage.
    """
    if country_col not in frame.columns:
        raise ValueError(f"Column {country_col!r} is required.")

    columns = _present_metrics(frame, metrics)
    records = []
    for country, group in frame.groupby(country_col, sort=False):
        n_rows = len(group)
        n_cells = n_rows * len(columns)
        n_missing = int(group[columns].isna().sum().sum()) if columns else 0
        records.append(
            {
                country_col: country,
                "n_rows": n_rows,
                "n_cells": n_cells,
                "n_missing": n_missing,
                "pct_missing": round(100.0 * n_missing / n_cells, 2) if n_cells else 0.0,
            }
        )
    out = pd.DataFrame.from_records(
        records, columns=[country_col, "n_rows", "n_cells", "n_missing", "pct_missing"]
    )
    out = out.sort_values("pct_missing", ascending=False).reset_index(drop=True)
    return cast(pd.DataFrame, out)


def write_missingness_report(
    frame: pd.DataFrame,
    output_path: Path,
    metrics: Sequence[str] = METRIC_COLUMNS,
    country_col: str = "country",
) -> Path:
    """Write a compact Markdown missingness report to disk."""
    by_metric = missingness_by_metric(frame, metrics)
    by_country = missingness_by_country(frame, metrics, country_col)

    lines = [
        "# Data Completeness Report",
        "",
        f"Rows analysed: **{len(frame)}**.",
        "",
        "## Missingness by metric",
        "",
        "| Metric | Missing | Total | % missing |",
        "| --- | ---: | ---: | ---: |",
    ]
    for _, row in by_metric.iterrows():
        lines.append(
            f"| {row['metric']} | {int(row['n_missing'])} | "
            f"{int(row['n_total'])} | {row['pct_missing']:.2f} |"
        )

    lines += [
        "",
        "## Missingness by country",
        "",
        "| Country | Rows | Missing cells | % missing |",
        "| --- | ---: | ---: | ---: |",
    ]
    for _, row in by_country.iterrows():
        lines.append(
            f"| {row[country_col]} | {int(row['n_rows'])} | "
            f"{int(row['n_missing'])} | {row['pct_missing']:.2f} |"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path
