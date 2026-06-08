"""Scenario projections and comparison tables.

A scenario is a constant annual growth rate applied to a country's last observed
value. This is deliberately simple and transparent: it answers "where does this
metric land if it grows/shrinks at X% per year?" -- useful for comparing a
business-as-usual path against reduction pathways.
"""

from __future__ import annotations

from collections.abc import Mapping

import pandas as pd

from carbon_transition_duckdb.forecasting.trend import _clean_pairs


def project_constant_growth(
    last_value: float, last_year: int, annual_rate: float, horizon: int
) -> list[tuple[int, float]]:
    """Project a value forward at a constant compounding annual rate."""
    return [
        (last_year + step, last_value * (1.0 + annual_rate) ** step)
        for step in range(1, horizon + 1)
    ]


def historical_cagr(
    frame: pd.DataFrame,
    country: str,
    metric: str,
    country_col: str = "country",
    year_col: str = "year",
) -> float:
    """Compound annual growth rate of a metric over a country's full history."""
    sub = frame[frame[country_col] == country].sort_values(year_col)
    pairs = _clean_pairs(sub[year_col].tolist(), sub[metric].tolist())
    if len(pairs) < 2:
        raise ValueError(f"{country!r} has too few {metric!r} observations.")
    (first_year, first_value) = pairs[0]
    (last_year, last_value) = pairs[-1]
    span = last_year - first_year
    if span <= 0 or first_value <= 0 or last_value <= 0:
        raise ValueError("Cannot compute CAGR from these values.")
    return float((last_value / first_value) ** (1.0 / span)) - 1.0


def default_scenarios(bau_rate: float) -> dict[str, float]:
    """A standard scenario set built around a business-as-usual rate."""
    return {
        "business_as_usual": round(bau_rate, 5),
        "flat": 0.0,
        "reduce_2pct": -0.02,
        "reduce_5pct": -0.05,
    }


def scenario_comparison(
    frame: pd.DataFrame,
    country: str,
    metric: str,
    scenarios: Mapping[str, float],
    horizon: int = 10,
    country_col: str = "country",
    year_col: str = "year",
) -> pd.DataFrame:
    """Project a metric under several annual-rate scenarios.

    Returns a frame indexed by year with one column per scenario, starting from
    the country's last observed value.
    """
    sub = frame[frame[country_col] == country].sort_values(year_col)
    pairs = _clean_pairs(sub[year_col].tolist(), sub[metric].tolist())
    if not pairs:
        raise ValueError(f"{country!r} has no {metric!r} observations.")
    last_year, last_value = int(pairs[-1][0]), pairs[-1][1]

    data: dict[str, list[float]] = {}
    index = [last_year + step for step in range(1, horizon + 1)]
    for name, rate in scenarios.items():
        path = project_constant_growth(last_value, last_year, rate, horizon)
        data[name] = [round(value, 4) for _, value in path]

    return pd.DataFrame(data, index=pd.Index(index, name="year"))
