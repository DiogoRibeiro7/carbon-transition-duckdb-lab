"""Peer-group benchmarking of transition-risk scores."""

from __future__ import annotations

from collections.abc import Iterable
from typing import cast

import pandas as pd

from carbon_transition_duckdb.quality.country_groups import filter_by_group
from carbon_transition_duckdb.risk.scoring import (
    ScoreWeights,
    add_driver_text,
    latest_year,
    score_transition_risk,
)


def benchmark_scores(
    scored: pd.DataFrame,
    year: int | None = None,
    score_col: str = "transition_risk_score",
    country_col: str = "country",
) -> pd.DataFrame:
    """Benchmark each country's score against its peers in one year.

    Parameters
    ----------
    scored:
        A scored frame (output of the scoring layer) restricted to the peer
        group of interest.
    year:
        Year to benchmark. Defaults to the latest available year.

    Returns
    -------
    pd.DataFrame
        One row per country with the score, ``risk_rank`` (1 = highest risk),
        ``peer_percentile`` (share of peers with higher risk; higher is a better
        position), the ``peer_median``, and the gaps to the median and to the
        peer leader (the lowest-risk peer).
    """
    for column in (score_col, country_col, "year"):
        if column not in scored.columns:
            raise ValueError(f"Column {column!r} is required.")

    target_year = year if year is not None else latest_year(scored)
    latest = scored.loc[
        scored["year"] == target_year, [country_col, score_col]
    ].copy()
    if latest.empty:
        raise ValueError(f"No rows found for year {target_year}.")

    n = len(latest)
    median = float(latest[score_col].median())
    leader = float(latest[score_col].min())
    scores = latest[score_col]

    latest["risk_rank"] = scores.rank(ascending=False, method="min").astype(int)
    latest["peer_percentile"] = scores.map(
        lambda value: round(100.0 * int((scores > value).sum()) / (n - 1), 1)
        if n > 1
        else 100.0
    )
    latest["peer_median"] = round(median, 2)
    latest["gap_to_median"] = (scores - median).round(2)
    latest["gap_to_leader"] = (scores - leader).round(2)

    out = latest.sort_values("risk_rank").reset_index(drop=True)
    return cast(pd.DataFrame, out)


def benchmark_group(
    mart: pd.DataFrame,
    group: str | Iterable[str] | None = None,
    weights: ScoreWeights | None = None,
    year: int | None = None,
) -> pd.DataFrame:
    """Score a peer group and benchmark its members.

    The score components are min-max scaled *within* the peer group, so the
    result is relative to comparable economies rather than the whole world.
    """
    frame = mart if group is None else filter_by_group(mart, group)
    scored = add_driver_text(score_transition_risk(frame, weights=weights))
    return benchmark_scores(scored, year=year)
