"""Tests for intensity decomposition and transition indicators."""

import math

import pandas as pd

from carbon_transition_duckdb.decomposition.indicators import transition_indicators
from carbon_transition_duckdb.decomposition.intensity import (
    intensity_decomposition,
    intensity_decomposition_frame,
)


def _frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "country": ["A", "A", "B", "B"],
            "year": [2010, 2020, 2010, 2020],
            "population": [1_000_000.0, 1_100_000.0, 500_000.0, 520_000.0],
            "co2": [50.0, 40.0, 20.0, 25.0],
            "primary_energy_consumption": [300.0, 280.0, 120.0, 140.0],
            "renewables_share_elec": [20.0, 45.0, 10.0, 15.0],
            "fossil_share_energy": [80.0, 55.0, 90.0, 85.0],
            "carbon_intensity": [0.166, 0.142, 0.166, 0.178],
        }
    )


def test_intensity_decomposition_is_exact() -> None:
    """Per-capita CO2 change splits exactly into the two factors."""
    result = intensity_decomposition(_frame(), "A", 2010, 2020)

    assert set(result.contributions) == {"energy_per_capita", "carbon_intensity"}
    assert math.isclose(sum(result.contributions.values()), result.delta, abs_tol=1e-9)
    assert abs(result.residual) < 1e-9


def test_intensity_frame() -> None:
    """The intensity frame helper returns exact rows for all countries."""
    out = intensity_decomposition_frame(_frame(), 2010, 2020)
    assert set(out["country"]) == {"A", "B"}
    assert (out["residual"].abs() < 1e-6).all()


def test_transition_indicators_columns_and_lockin() -> None:
    """Indicators should rank faster fossil decline as lower lock-in."""
    out = transition_indicators(_frame(), 2010, 2020).set_index("country")

    assert "fossil_lockin_index" in out.columns
    assert "renewables_share_elec_change" in out.columns
    # A's fossil share falls faster than B's, so A has lower lock-in.
    assert out.loc["A", "fossil_lockin_index"] < out.loc["B", "fossil_lockin_index"]
    # Renewable change is reported correctly.
    assert math.isclose(out.loc["A", "renewables_share_elec_change"], 25.0)


def test_transition_indicators_annual_decline_sign() -> None:
    """A falling fossil share yields a positive annual decline."""
    out = transition_indicators(_frame(), 2010, 2020).set_index("country")
    assert out.loc["A", "fossil_annual_decline"] > 0
