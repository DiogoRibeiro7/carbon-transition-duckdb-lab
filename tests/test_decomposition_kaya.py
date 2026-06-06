"""Tests for the Kaya identity decomposition."""

import math

import pandas as pd

from carbon_transition_duckdb.decomposition.kaya import (
    kaya_decomposition,
    kaya_decomposition_frame,
)


def _frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "country": ["A", "A", "B", "B"],
            "year": [2010, 2020, 2010, 2020],
            "population": [1_000_000.0, 1_100_000.0, 500_000.0, 520_000.0],
            "co2": [50.0, 40.0, 20.0, 25.0],
            "primary_energy_consumption": [300.0, 280.0, 120.0, 140.0],
        }
    )


def test_kaya_three_factor_is_exact() -> None:
    """Without GDP the three contributions sum exactly to the CO2 change."""
    result = kaya_decomposition(_frame(), "A", 2010, 2020)

    assert set(result.contributions) == {
        "population",
        "energy_per_capita",
        "carbon_intensity",
    }
    assert math.isclose(result.delta, -10.0)
    assert math.isclose(sum(result.contributions.values()), result.delta, abs_tol=1e-9)
    assert abs(result.residual) < 1e-9


def test_kaya_four_factor_with_gdp() -> None:
    """With GDP present the decomposition uses affluence + energy intensity."""
    frame = _frame()
    frame["gdp"] = [2.0e10, 2.5e10, 8.0e9, 9.0e9]

    result = kaya_decomposition(frame, "A", 2010, 2020)

    assert set(result.contributions) == {
        "population",
        "affluence",
        "energy_intensity",
        "carbon_intensity",
    }
    assert abs(result.residual) < 1e-9


def test_kaya_frame_covers_all_countries() -> None:
    """The frame helper returns one exact row per country."""
    out = kaya_decomposition_frame(_frame(), 2010, 2020)

    assert set(out["country"]) == {"A", "B"}
    assert (out["residual"].abs() < 1e-6).all()
    assert "carbon_intensity_effect" in out.columns


def test_kaya_missing_year_raises() -> None:
    """A country without both endpoints raises a clear error."""
    try:
        kaya_decomposition(_frame(), "A", 2010, 2099)
    except ValueError as exc:
        assert "2099" in str(exc)
    else:
        raise AssertionError("Expected ValueError for a missing endpoint year.")
