"""Tests for scenario projections and target-gap analysis."""

import math

import pandas as pd
import pytest

from carbon_transition_duckdb.forecasting.scenarios import (
    default_scenarios,
    historical_cagr,
    project_constant_growth,
    scenario_comparison,
)
from carbon_transition_duckdb.forecasting.targets import (
    ReductionTarget,
    target_gap,
    target_gap_frame,
)


def _frame() -> pd.DataFrame:
    # A: steady -1/yr decline; B: flat.
    return pd.DataFrame(
        {
            "country": ["A", "A", "A", "A", "B", "B", "B", "B"],
            "year": [2010, 2011, 2012, 2013, 2010, 2011, 2012, 2013],
            "co2": [13.0, 12.0, 11.0, 10.0, 20.0, 20.0, 20.0, 20.0],
        }
    )


def test_project_constant_growth() -> None:
    """Compounding a rate forward yields the expected path."""
    path = project_constant_growth(100.0, 2020, -0.10, 2)
    assert path[0] == (2021, 90.0)
    assert math.isclose(path[1][1], 81.0)


def test_historical_cagr_sign() -> None:
    """A declining series has a negative CAGR."""
    assert historical_cagr(_frame(), "A", "co2") < 0


def test_default_scenarios_keys() -> None:
    """The default scenario set includes a BAU plus reduction paths."""
    scenarios = default_scenarios(-0.01)
    assert "business_as_usual" in scenarios
    assert scenarios["flat"] == 0.0
    assert scenarios["reduce_5pct"] == -0.05


def test_scenario_comparison_shape() -> None:
    """Scenario comparison returns one column per scenario over the horizon."""
    out = scenario_comparison(_frame(), "A", "co2", default_scenarios(-0.02), horizon=4)
    assert list(out.index) == [2014, 2015, 2016, 2017]
    assert "business_as_usual" in out.columns
    # The flat scenario holds the last observed value (10.0).
    assert (out["flat"] == 10.0).all()


def test_target_gap_on_track_and_missed() -> None:
    """A declining country can meet a target; a flat one misses it."""
    target = ReductionTarget(metric="co2", base_year=2010, target_year=2016, reduction=0.30)

    gap_a = target_gap(_frame(), "A", target)
    # A: base 13 -> target 9.1; trend projects ~7 by 2016 -> on track.
    assert gap_a.on_track
    assert gap_a.gap < 0

    gap_b = target_gap(_frame(), "B", target)
    # B: base 20 -> target 14; flat projection 20 -> missed.
    assert not gap_b.on_track
    assert math.isclose(gap_b.target_value, 14.0)


def test_reduction_target_validation() -> None:
    """Invalid targets raise on construction."""
    with pytest.raises(ValueError):
        ReductionTarget(metric="co2", base_year=2020, target_year=2010, reduction=0.5)
    with pytest.raises(ValueError):
        ReductionTarget(metric="co2", base_year=2010, target_year=2030, reduction=1.5)


def test_target_gap_frame_columns() -> None:
    """The frame helper returns a row per country with gap fields."""
    target = ReductionTarget(metric="co2", base_year=2010, target_year=2016, reduction=0.30)
    out = target_gap_frame(_frame(), target).set_index("country")
    assert {"target_value", "projected_value", "gap", "gap_pct", "on_track"}.issubset(
        out.columns
    )
    assert set(out.index) == {"A", "B"}
