"""Monte Carlo uncertainty for transition-risk scores.

The transition-risk score is a weighted sum of min-max scaled components, so a
single set of weights produces a single point estimate and ranking. How robust
is that ranking to the *choice of weights*?

This module answers that by perturbing the weights many times around a chosen
profile (Dirichlet samples whose mean is the profile), rescoring each time, and
summarising the distribution of each country's score and rank. The result gives
honest confidence bands and rank-stability flags instead of false precision.

Everything is pure-Python and deterministic given the seed -- no extra
dependencies and reproducible runs.
"""

from __future__ import annotations

import math
import random
from typing import cast

import pandas as pd

from carbon_transition_duckdb.risk.scoring import (
    ScoreWeights,
    latest_year,
    score_transition_risk,
)

_FIELDS = (
    "co2_trend",
    "co2_per_capita",
    "carbon_intensity",
    "fossil_share",
    "renewable_gap",
)


def sample_weights(
    base: ScoreWeights, concentration: float, rng: random.Random
) -> ScoreWeights:
    """Draw a Dirichlet-perturbed weight vector centred on ``base``.

    Higher ``concentration`` keeps samples tighter around the base profile. The
    returned weights are non-negative and sum to 1, so they pass validation.
    """
    alphas = [max(getattr(base, field) * concentration, 1e-9) for field in _FIELDS]
    gammas = [rng.gammavariate(alpha, 1.0) for alpha in alphas]
    total = sum(gammas) or 1.0
    values = [gamma / total for gamma in gammas]
    # Pin the last component so the five sum to exactly 1.0 (float-safe).
    values[-1] = 1.0 - sum(values[:-1])
    if values[-1] < 0.0:
        clipped = [max(value, 0.0) for value in values]
        scale = sum(clipped) or 1.0
        values = [value / scale for value in clipped]
        values[-1] = 1.0 - sum(values[:-1])
    return ScoreWeights(**dict(zip(_FIELDS, values, strict=True)))


def _percentile(sorted_values: list[float], q: float) -> float:
    """Linear-interpolated percentile of a pre-sorted list (q in 0..100)."""
    if not sorted_values:
        return math.nan
    if len(sorted_values) == 1:
        return sorted_values[0]
    rank = (q / 100.0) * (len(sorted_values) - 1)
    low = math.floor(rank)
    high = math.ceil(rank)
    if low == high:
        return sorted_values[int(rank)]
    frac = rank - low
    return sorted_values[low] * (1.0 - frac) + sorted_values[high] * frac


def run_weight_samples(
    frame: pd.DataFrame,
    base: ScoreWeights,
    n_samples: int,
    concentration: float,
    seed: int,
    year: int | None,
) -> tuple[int, dict[str, list[float]], dict[str, list[int]]]:
    """Rescore ``frame`` under many perturbed weight vectors.

    Returns the analysed year and, per country, the list of sampled scores and
    sampled ranks (1 = highest risk) in that year.
    """
    target_year = year if year is not None else latest_year(frame)
    countries = sorted(
        str(c) for c in frame.loc[frame["year"] == target_year, "country"].unique()
    )
    scores: dict[str, list[float]] = {country: [] for country in countries}
    ranks: dict[str, list[int]] = {country: [] for country in countries}

    rng = random.Random(seed)
    for _ in range(n_samples):
        weights = sample_weights(base, concentration, rng)
        scored = score_transition_risk(frame, weights=weights)
        latest = scored.loc[
            scored["year"] == target_year, ["country", "transition_risk_score"]
        ]
        rank_series = latest["transition_risk_score"].rank(
            ascending=False, method="min"
        )
        for (_, row), rank in zip(latest.iterrows(), rank_series, strict=True):
            country = str(row["country"])
            scores[country].append(float(row["transition_risk_score"]))
            ranks[country].append(int(rank))

    return target_year, scores, ranks


def uncertainty_summary(
    frame: pd.DataFrame,
    weights: ScoreWeights | None = None,
    n_samples: int = 500,
    concentration: float = 60.0,
    seed: int = 42,
    year: int | None = None,
    top_k: int = 3,
    rank_uncertain_span: int = 2,
) -> pd.DataFrame:
    """Summarise score and rank uncertainty under weight perturbation.

    Returns one row per country with the mean score, a 5th-95th percentile score
    band, the median/low/high rank, the probability of landing in the top-``k``
    (highest risk), and a ``rank_uncertain`` flag set when the 90% rank band is
    wider than ``rank_uncertain_span``.
    """
    base = weights or ScoreWeights()
    base.validate()

    _, scores, ranks = run_weight_samples(
        frame, base, n_samples, concentration, seed, year
    )

    records: list[dict[str, float | str | bool]] = []
    for country, sampled_scores in scores.items():
        sorted_scores = sorted(sampled_scores)
        sampled_ranks = ranks[country]
        sorted_ranks = sorted(float(r) for r in sampled_ranks)
        n = len(sorted_scores)
        rank_low = round(_percentile(sorted_ranks, 5))
        rank_high = round(_percentile(sorted_ranks, 95))
        prob_top_k = sum(1 for r in sampled_ranks if r <= top_k) / n if n else 0.0
        records.append(
            {
                "country": country,
                "score_mean": round(sum(sorted_scores) / n, 2) if n else 0.0,
                "score_low": round(_percentile(sorted_scores, 5), 2),
                "score_high": round(_percentile(sorted_scores, 95), 2),
                "rank_median": round(_percentile(sorted_ranks, 50), 1),
                "rank_low": int(rank_low),
                "rank_high": int(rank_high),
                "prob_top_k": round(prob_top_k, 3),
                "rank_uncertain": (rank_high - rank_low) > rank_uncertain_span,
            }
        )

    out = pd.DataFrame.from_records(records)
    out = out.sort_values("score_mean", ascending=False).reset_index(drop=True)
    return cast(pd.DataFrame, out)
