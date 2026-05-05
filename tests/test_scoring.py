"""Tests for transition-risk scoring."""

import pandas as pd

from carbon_transition_duckdb.risk.scoring import (
    ScoreWeights,
    add_driver_text,
    score_transition_risk,
)


def _frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "country": ["A", "A", "B", "B", "C", "C"],
            "year": [2020, 2021, 2020, 2021, 2020, 2021],
            "co2": [10.0, 11.0, 30.0, 45.0, 5.0, 4.0],
            "co2_per_capita": [1.0, 1.1, 4.0, 5.0, 0.5, 0.4],
            "carbon_intensity": [0.1, 0.11, 0.4, 0.5, 0.05, 0.04],
            "fossil_share_energy": [30.0, 32.0, 80.0, 82.0, 20.0, 18.0],
            "renewables_share_elec": [50.0, 52.0, 10.0, 9.0, 80.0, 82.0],
        }
    )


def test_score_transition_risk_outputs_score_column() -> None:
    """Scoring should add bounded component and final score columns."""
    scored = score_transition_risk(_frame())

    assert "transition_risk_score" in scored.columns
    assert scored["transition_risk_score"].between(0, 100).all()


def test_score_transition_risk_flags_higher_risk_entity() -> None:
    """Entity B should score above entity C in the latest year."""
    scored = score_transition_risk(_frame())
    latest = scored.loc[scored["year"] == 2021].set_index("country")

    assert latest.loc["B", "transition_risk_score"] > latest.loc["C", "transition_risk_score"]


def test_add_driver_text_adds_interpretable_labels() -> None:
    """Driver text should provide readable explanations."""
    scored = add_driver_text(score_transition_risk(_frame()))

    assert "risk_drivers" in scored.columns
    assert scored["risk_drivers"].str.len().gt(0).all()


def test_score_weights_validate_sum() -> None:
    """Score weights must sum to 1."""
    bad_weights = ScoreWeights(co2_trend=0.5)

    try:
        bad_weights.validate()
    except ValueError as exc:
        assert "sum to 1" in str(exc)
    else:
        raise AssertionError("Expected invalid weights to fail validation.")
