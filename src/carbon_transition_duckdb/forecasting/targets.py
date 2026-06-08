"""Policy target gap analysis.

A reduction target is expressed as "cut <metric> by <reduction> relative to its
<base_year> level by <target_year>". This module computes the implied target
level, projects the metric to the target year with the baseline trend, and
reports the gap between the projection and the target.

The analysis is descriptive: it measures distance to a stated target under a
trend-continuation assumption. It is not a forecast of policy outcomes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

import pandas as pd

from carbon_transition_duckdb.forecasting.trend import _clean_pairs, fit_linear_trend


@dataclass(frozen=True)
class ReductionTarget:
    """A proportional reduction target for a metric."""

    metric: str
    base_year: int
    target_year: int
    reduction: float  # fraction, e.g. 0.55 for a 55% cut

    def __post_init__(self) -> None:
        if not 0.0 <= self.reduction <= 1.0:
            raise ValueError("reduction must be a fraction between 0 and 1.")
        if self.target_year <= self.base_year:
            raise ValueError("target_year must be after base_year.")


@dataclass(frozen=True)
class TargetGap:
    """The gap between a trend projection and a reduction target."""

    country: str
    base_value: float
    target_value: float
    projected_value: float

    @property
    def gap(self) -> float:
        """Projected minus target (positive means the target is missed)."""
        return self.projected_value - self.target_value

    @property
    def gap_pct(self) -> float:
        """Gap as a percentage of the target level."""
        return 100.0 * self.gap / self.target_value if self.target_value else 0.0

    @property
    def on_track(self) -> bool:
        """True when the projection meets or beats the target."""
        return self.projected_value <= self.target_value


def _value_at(pairs: list[tuple[float, float]], year: int) -> float | None:
    """Exact value at a year, if present."""
    for x, y in pairs:
        if int(x) == year:
            return y
    return None


def target_gap(
    frame: pd.DataFrame,
    country: str,
    target: ReductionTarget,
    country_col: str = "country",
    year_col: str = "year",
    min_obs: int = 3,
) -> TargetGap:
    """Compute the gap to a reduction target for one country."""
    sub = frame[frame[country_col] == country].sort_values(year_col)
    pairs = _clean_pairs(sub[year_col].tolist(), sub[target.metric].tolist())
    if len(pairs) < min_obs:
        raise ValueError(f"{country!r} has too few {target.metric!r} observations.")

    base_value = _value_at(pairs, target.base_year)
    if base_value is None:
        raise ValueError(f"{country!r} has no {target.base_year} base-year value.")

    trend = fit_linear_trend([x for x, _ in pairs], [y for _, y in pairs], min_obs)
    projected = trend.predict(target.target_year)
    target_value = base_value * (1.0 - target.reduction)

    return TargetGap(
        country=country,
        base_value=base_value,
        target_value=target_value,
        projected_value=projected,
    )


def target_gap_frame(
    frame: pd.DataFrame,
    target: ReductionTarget,
    country_col: str = "country",
    year_col: str = "year",
    min_obs: int = 3,
) -> pd.DataFrame:
    """Compute target gaps for every country with enough data."""
    records: list[dict[str, float | str | bool]] = []
    for country in sorted(frame[country_col].dropna().unique()):
        try:
            result = target_gap(
                frame,
                str(country),
                target,
                country_col=country_col,
                year_col=year_col,
                min_obs=min_obs,
            )
        except ValueError:
            continue
        records.append(
            {
                "country": result.country,
                "base_value": round(result.base_value, 4),
                "target_value": round(result.target_value, 4),
                "projected_value": round(result.projected_value, 4),
                "gap": round(result.gap, 4),
                "gap_pct": round(result.gap_pct, 2),
                "on_track": result.on_track,
            }
        )
    return cast(pd.DataFrame, pd.DataFrame.from_records(records))
