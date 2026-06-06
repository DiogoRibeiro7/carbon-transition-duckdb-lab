"""Shared frame helpers for the decomposition layer."""

from __future__ import annotations

import pandas as pd


def resolve_year_bounds(
    frame: pd.DataFrame,
    year_col: str,
    start_year: int | None,
    end_year: int | None,
) -> tuple[int, int]:
    """Resolve start/end years, defaulting to the min/max present in the frame."""
    years = pd.to_numeric(frame[year_col], errors="coerce").dropna()
    if years.empty:
        raise ValueError("No valid years available for decomposition.")
    low = int(years.min()) if start_year is None else start_year
    high = int(years.max()) if end_year is None else end_year
    if low == high:
        raise ValueError("start_year and end_year must differ.")
    return low, high


def two_year_rows(
    country_frame: pd.DataFrame,
    year_col: str,
    start_year: int,
    end_year: int,
) -> tuple[pd.Series, pd.Series] | None:
    """Return the (start, end) rows for one country, or None if either is absent."""
    start = country_frame[country_frame[year_col] == start_year]
    end = country_frame[country_frame[year_col] == end_year]
    if start.empty or end.empty:
        return None
    return start.iloc[0], end.iloc[0]
