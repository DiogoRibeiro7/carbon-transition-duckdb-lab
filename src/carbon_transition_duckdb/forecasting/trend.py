"""Baseline ordinary-least-squares trend forecasts with uncertainty intervals.

The forecasts are intentionally simple and transparent: a straight line fit to a
country's history by ordinary least squares, extrapolated forward. Uncertainty
is reported as an approximate prediction interval using the standard error of
prediction and a normal (z) multiplier.

These are baseline screening projections, not calibrated climate scenarios. They
assume the recent linear trend continues and make no causal or policy claims.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import cast

import pandas as pd

Z_95 = 1.959963984540054  # standard-normal quantile for a 95% interval


def _clean_pairs(
    years: Sequence[float], values: Sequence[float]
) -> list[tuple[float, float]]:
    """Return (year, value) pairs dropping any with a missing value."""
    pairs: list[tuple[float, float]] = []
    for year, value in zip(years, values, strict=True):
        if value is None:
            continue
        fvalue = float(value)
        if math.isnan(fvalue):
            continue
        pairs.append((float(year), fvalue))
    return pairs


@dataclass(frozen=True)
class LinearTrend:
    """An ordinary-least-squares line fit ``y = intercept + slope * year``."""

    slope: float
    intercept: float
    r_squared: float
    residual_se: float
    n_obs: int
    x_mean: float
    sxx: float

    def predict(self, year: float) -> float:
        """Point forecast for a year."""
        return self.intercept + self.slope * year

    def predict_interval(
        self, year: float, z: float = Z_95
    ) -> tuple[float, float, float]:
        """Return ``(forecast, lower, upper)`` for a year.

        The half-width uses the standard error of an individual prediction:
        ``s * sqrt(1 + 1/n + (year - x_mean)^2 / Sxx)``.
        """
        forecast = self.predict(year)
        se = self.residual_se * math.sqrt(
            1.0 + 1.0 / self.n_obs + (year - self.x_mean) ** 2 / self.sxx
        )
        return forecast, forecast - z * se, forecast + z * se


def fit_linear_trend(
    years: Sequence[float], values: Sequence[float], min_obs: int = 3
) -> LinearTrend:
    """Fit a least-squares line to a series, ignoring missing values."""
    pairs = _clean_pairs(years, values)
    n = len(pairs)
    if n < min_obs:
        raise ValueError(f"Need at least {min_obs} observations, got {n}.")

    xs = [x for x, _ in pairs]
    ys = [y for _, y in pairs]
    x_mean = sum(xs) / n
    y_mean = sum(ys) / n
    sxx = sum((x - x_mean) ** 2 for x in xs)
    if sxx == 0.0:
        raise ValueError("All observations share the same year; cannot fit a trend.")
    sxy = sum((x - x_mean) * (y - y_mean) for x, y in pairs)

    slope = sxy / sxx
    intercept = y_mean - slope * x_mean
    sse = sum((y - (intercept + slope * x)) ** 2 for x, y in pairs)
    sst = sum((y - y_mean) ** 2 for y in ys)
    r_squared = 1.0 - sse / sst if sst > 0 else 0.0
    residual_se = math.sqrt(sse / (n - 2)) if n > 2 else 0.0

    return LinearTrend(
        slope=slope,
        intercept=intercept,
        r_squared=r_squared,
        residual_se=residual_se,
        n_obs=n,
        x_mean=x_mean,
        sxx=sxx,
    )


def forecast_metric(
    frame: pd.DataFrame,
    country: str,
    metric: str,
    horizon: int = 5,
    country_col: str = "country",
    year_col: str = "year",
    z: float = Z_95,
    min_obs: int = 3,
) -> pd.DataFrame:
    """Forecast a metric for one country ``horizon`` years past its last year."""
    if metric not in frame.columns:
        raise ValueError(f"Column {metric!r} is required.")
    sub = frame[frame[country_col] == country].sort_values(year_col)
    pairs = _clean_pairs(sub[year_col].tolist(), sub[metric].tolist())
    if len(pairs) < min_obs:
        raise ValueError(f"{country!r} has too few {metric!r} observations.")

    trend = fit_linear_trend([x for x, _ in pairs], [y for _, y in pairs], min_obs)
    last_year = int(max(x for x, _ in pairs))

    records = []
    for step in range(1, horizon + 1):
        year = last_year + step
        forecast, lower, upper = trend.predict_interval(year, z=z)
        records.append(
            {
                "country": country,
                "year": year,
                "forecast": round(forecast, 4),
                "lower": round(lower, 4),
                "upper": round(upper, 4),
            }
        )
    return cast(pd.DataFrame, pd.DataFrame.from_records(records))


def forecast_frame(
    frame: pd.DataFrame,
    metric: str,
    horizon: int = 5,
    country_col: str = "country",
    year_col: str = "year",
    z: float = Z_95,
    min_obs: int = 3,
) -> pd.DataFrame:
    """Forecast a metric for every country with enough observations."""
    parts: list[pd.DataFrame] = []
    for country in sorted(frame[country_col].dropna().unique()):
        try:
            parts.append(
                forecast_metric(
                    frame,
                    str(country),
                    metric,
                    horizon,
                    country_col=country_col,
                    year_col=year_col,
                    z=z,
                    min_obs=min_obs,
                )
            )
        except ValueError:
            continue
    if not parts:
        return pd.DataFrame(columns=["country", "year", "forecast", "lower", "upper"])
    return pd.concat(parts, ignore_index=True)


def trend_table(
    frame: pd.DataFrame,
    metric: str,
    country_col: str = "country",
    year_col: str = "year",
    min_obs: int = 3,
) -> pd.DataFrame:
    """Summarise each country's fitted trend (slope, R^2, annual change)."""
    records: list[dict[str, float | str]] = []
    for country in sorted(frame[country_col].dropna().unique()):
        sub = frame[frame[country_col] == country].sort_values(year_col)
        pairs = _clean_pairs(sub[year_col].tolist(), sub[metric].tolist())
        if len(pairs) < min_obs:
            continue
        trend = fit_linear_trend([x for x, _ in pairs], [y for _, y in pairs], min_obs)
        records.append(
            {
                "country": str(country),
                "annual_change": round(trend.slope, 4),
                "r_squared": round(trend.r_squared, 3),
                "n_obs": trend.n_obs,
            }
        )
    return cast(pd.DataFrame, pd.DataFrame.from_records(records))
