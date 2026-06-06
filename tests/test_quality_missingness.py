"""Tests for missingness reporting."""

import pandas as pd

from carbon_transition_duckdb.quality.missingness import (
    missingness_by_country,
    missingness_by_metric,
    write_missingness_report,
)

NaN = float("nan")


def _frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "country": ["A", "A", "B", "B"],
            "year": [2020, 2021, 2020, 2021],
            "co2": [1.0, NaN, 3.0, 4.0],
            "co2_per_capita": [NaN, NaN, 0.3, 0.4],
        }
    )


def test_missingness_by_metric_counts_nulls() -> None:
    """Per-metric counts should reflect the injected NaNs."""
    report = missingness_by_metric(_frame(), metrics=["co2", "co2_per_capita"])
    by_metric = report.set_index("metric")

    assert by_metric.loc["co2", "n_missing"] == 1
    assert by_metric.loc["co2_per_capita", "n_missing"] == 2
    assert by_metric.loc["co2_per_capita", "pct_missing"] == 50.0


def test_missingness_by_country_counts_cells() -> None:
    """Country A has 3 missing metric cells out of 4."""
    report = missingness_by_country(_frame(), metrics=["co2", "co2_per_capita"])
    by_country = report.set_index("country")

    assert by_country.loc["A", "n_missing"] == 3
    assert by_country.loc["A", "n_cells"] == 4
    assert by_country.loc["B", "n_missing"] == 0


def test_write_missingness_report(tmp_path) -> None:
    """The Markdown report should be written and mention both sections."""
    out = write_missingness_report(
        _frame(), tmp_path / "completeness.md", metrics=["co2", "co2_per_capita"]
    )
    text = out.read_text(encoding="utf-8")

    assert out.exists()
    assert "Missingness by metric" in text
    assert "Missingness by country" in text
