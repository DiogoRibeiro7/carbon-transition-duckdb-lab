"""Tests for Monte Carlo uncertainty-aware scoring."""

import random

import pandas as pd

from carbon_transition_duckdb.risk.scoring import ScoreWeights
from carbon_transition_duckdb.uncertainty.montecarlo import (
    _percentile,
    sample_weights,
    uncertainty_summary,
)


def _frame() -> pd.DataFrame:
    # B is clearly highest risk, C clearly lowest, A in between.
    return pd.DataFrame(
        {
            "country": ["A", "A", "B", "B", "C", "C"],
            "year": [2023, 2024, 2023, 2024, 2023, 2024],
            "co2": [10.0, 11.0, 30.0, 45.0, 5.0, 4.0],
            "co2_per_capita": [1.0, 1.1, 4.0, 5.0, 0.5, 0.4],
            "carbon_intensity": [0.1, 0.11, 0.4, 0.5, 0.05, 0.04],
            "fossil_share_energy": [30.0, 32.0, 80.0, 82.0, 20.0, 18.0],
            "renewables_share_elec": [50.0, 52.0, 10.0, 9.0, 80.0, 82.0],
        }
    )


def test_percentile_interpolates() -> None:
    """_percentile returns interpolated values for a sorted list."""
    values = [0.0, 10.0, 20.0, 30.0, 40.0]
    assert _percentile(values, 0) == 0.0
    assert _percentile(values, 100) == 40.0
    assert _percentile(values, 50) == 20.0


def test_sample_weights_valid_and_deterministic() -> None:
    """Sampled weights are valid (sum to 1) and reproducible by seed."""
    base = ScoreWeights()
    w1 = sample_weights(base, concentration=60.0, rng=random.Random(1))
    w2 = sample_weights(base, concentration=60.0, rng=random.Random(1))

    w1.validate()  # must not raise
    assert w1 == w2  # same seed -> identical


def test_sample_weights_mean_near_base() -> None:
    """Averaging many Dirichlet samples recovers the base weights approximately."""
    base = ScoreWeights()
    rng = random.Random(0)
    samples = [sample_weights(base, 60.0, rng) for _ in range(400)]
    mean_trend = sum(w.co2_trend for w in samples) / len(samples)
    assert abs(mean_trend - base.co2_trend) < 0.05


def test_uncertainty_summary_columns_and_bands() -> None:
    """Summary has ordered score bands and valid probabilities."""
    out = uncertainty_summary(_frame(), n_samples=120, seed=3)

    expected = {
        "country",
        "score_mean",
        "score_low",
        "score_high",
        "rank_median",
        "rank_low",
        "rank_high",
        "prob_top_k",
        "rank_uncertain",
    }
    assert expected <= set(out.columns)
    assert (out["score_low"] <= out["score_mean"]).all()
    assert (out["score_mean"] <= out["score_high"]).all()
    assert (out["rank_low"] <= out["rank_high"]).all()
    assert out["prob_top_k"].between(0.0, 1.0).all()


def test_uncertainty_summary_flags_dominant_country() -> None:
    """The clearly-highest-risk country is reliably ranked first."""
    out = uncertainty_summary(_frame(), n_samples=200, seed=5).set_index("country")

    assert out.loc["B", "prob_top_k"] == 1.0
    assert out.loc["B", "rank_low"] == 1
    assert not bool(out.loc["B", "rank_uncertain"])


def test_uncertainty_summary_is_reproducible() -> None:
    """Same seed yields identical output."""
    a = uncertainty_summary(_frame(), n_samples=80, seed=11)
    b = uncertainty_summary(_frame(), n_samples=80, seed=11)
    pd.testing.assert_frame_equal(a, b)
