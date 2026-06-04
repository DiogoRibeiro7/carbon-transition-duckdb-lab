"""Transparent carbon-transition risk scoring.

The scoring functions are intentionally simple. They are designed for
interpretability, auditing, and exploratory analysis, not for causal inference.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import cast

import pandas as pd


@dataclass(frozen=True)
class ScoreWeights:
    """Weights used by the transition-risk score."""

    co2_trend: float = 0.30
    co2_per_capita: float = 0.20
    carbon_intensity: float = 0.20
    fossil_share: float = 0.20
    renewable_gap: float = 0.10

    def validate(self) -> None:
        """Validate that all weights are non-negative and sum to 1."""
        values = [
            self.co2_trend,
            self.co2_per_capita,
            self.carbon_intensity,
            self.fossil_share,
            self.renewable_gap,
        ]
        if any(weight < 0 for weight in values):
            raise ValueError("All score weights must be non-negative.")
        if abs(sum(values) - 1.0) > 1e-9:
            raise ValueError("Score weights must sum to 1.")


def minmax_score(series: pd.Series, higher_is_risk: bool = True) -> pd.Series:
    """Scale a numeric series to a 0-100 score.

    Missing values are preserved until the final fill step in
    :func:`score_transition_risk`.
    """
    numeric = pd.to_numeric(series, errors="coerce")
    valid = numeric.dropna()

    if valid.empty:
        return pd.Series([0.0] * len(series), index=series.index)

    minimum = valid.min()
    maximum = valid.max()
    if maximum == minimum:
        scaled = pd.Series([50.0] * len(series), index=series.index)
    else:
        scaled = 100.0 * (numeric - minimum) / (maximum - minimum)

    if not higher_is_risk:
        scaled = 100.0 - scaled

    return scaled


def add_recent_trend(
    frame: pd.DataFrame,
    group_col: str = "country",
    year_col: str = "year",
    value_col: str = "co2",
    output_col: str = "co2_recent_trend",
    periods: int = 5,
) -> pd.DataFrame:
    """Add a recent change column by group.

    The trend is a simple difference between the current value and the value
    `periods` rows before within each group.
    """
    required = {group_col, year_col, value_col}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    output = frame.sort_values([group_col, year_col]).copy()
    output[output_col] = (
        output.groupby(group_col, sort=False)[value_col]
        .transform(lambda values: values - values.shift(periods))
        .fillna(0.0)
    )
    return cast(pd.DataFrame, output)


def score_transition_risk(
    frame: pd.DataFrame,
    weights: ScoreWeights | None = None,
) -> pd.DataFrame:
    """Compute a transparent transition-risk score.

    Parameters
    ----------
    frame:
        DataFrame with country-year transition metrics.
    weights:
        Score weights. Defaults to :class:`ScoreWeights`.

    Returns
    -------
    pd.DataFrame
        Input frame with component scores and final transition_risk_score.
    """
    weights = weights or ScoreWeights()
    weights.validate()

    required = {
        "country",
        "year",
        "co2",
        "co2_per_capita",
        "carbon_intensity",
        "fossil_share_energy",
        "renewables_share_elec",
    }
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    scored = add_recent_trend(frame)
    scored["co2_trend_score"] = minmax_score(scored["co2_recent_trend"], higher_is_risk=True)
    scored["co2_per_capita_score"] = minmax_score(scored["co2_per_capita"], higher_is_risk=True)
    scored["carbon_intensity_score"] = minmax_score(scored["carbon_intensity"], higher_is_risk=True)
    scored["fossil_share_score"] = minmax_score(
        scored["fossil_share_energy"], higher_is_risk=True
    )
    scored["renewable_gap_score"] = minmax_score(
        scored["renewables_share_elec"], higher_is_risk=False
    )

    component_cols = [
        "co2_trend_score",
        "co2_per_capita_score",
        "carbon_intensity_score",
        "fossil_share_score",
        "renewable_gap_score",
    ]
    scored[component_cols] = scored[component_cols].fillna(0.0)

    scored["transition_risk_score"] = (
        weights.co2_trend * scored["co2_trend_score"]
        + weights.co2_per_capita * scored["co2_per_capita_score"]
        + weights.carbon_intensity * scored["carbon_intensity_score"]
        + weights.fossil_share * scored["fossil_share_score"]
        + weights.renewable_gap * scored["renewable_gap_score"]
    ).round(2)

    return scored


def top_risk_drivers(row: pd.Series, max_drivers: int = 3) -> list[str]:
    """Return human-readable drivers for a scored row."""
    candidates = [
        ("co2_trend_score", "recent CO2 emissions trend"),
        ("co2_per_capita_score", "high CO2 per capita"),
        ("carbon_intensity_score", "high carbon intensity"),
        ("fossil_share_score", "high fossil-fuel share"),
        ("renewable_gap_score", "low renewable electricity share"),
    ]

    ordered = sorted(
        candidates,
        key=lambda item: float(row.get(item[0], 0.0) or 0.0),
        reverse=True,
    )
    return [label for _, label in ordered[:max_drivers]]


def add_driver_text(frame: pd.DataFrame, max_drivers: int = 3) -> pd.DataFrame:
    """Add a text column with the dominant risk drivers."""
    output = frame.copy()
    output["risk_drivers"] = [
        "; ".join(top_risk_drivers(row, max_drivers=max_drivers))
        for _, row in output.iterrows()
    ]
    return cast(pd.DataFrame, output)


def latest_year(frame: pd.DataFrame, year_col: str = "year") -> int:
    """Return the latest available year in a DataFrame."""
    if year_col not in frame.columns:
        raise ValueError(f"Column {year_col!r} is missing.")
    years = pd.to_numeric(frame[year_col], errors="coerce").dropna()
    if years.empty:
        raise ValueError("No valid years available.")
    return int(years.max())


def filter_entities(
    frame: pd.DataFrame, excluded_entities: Iterable[str] | None = None
) -> pd.DataFrame:
    """Remove aggregate entities if present.

    OWID files include aggregate rows such as World, Europe, and Asia. This
    helper is intentionally configurable because some analyses may want to
    keep those aggregates.
    """
    excluded = set(
        excluded_entities
        or {"World", "Europe", "Asia", "Africa", "North America", "South America"}
    )
    if "country" not in frame.columns:
        raise ValueError("Column 'country' is required.")
    return cast(pd.DataFrame, frame.loc[~frame["country"].isin(excluded)].copy())
