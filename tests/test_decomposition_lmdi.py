"""Tests for the LMDI primitives."""

import math

from carbon_transition_duckdb.decomposition.lmdi import (
    Decomposition,
    log_ratio,
    logarithmic_mean,
)


def test_logarithmic_mean_equal_values() -> None:
    """L(a, a) == a."""
    assert logarithmic_mean(5.0, 5.0) == 5.0


def test_logarithmic_mean_between_values() -> None:
    """The logarithmic mean lies between the two inputs."""
    value = logarithmic_mean(1.0, math.e)
    assert 1.0 < value < math.e


def test_logarithmic_mean_non_positive_is_zero() -> None:
    """Non-positive inputs degrade to zero."""
    assert logarithmic_mean(0.0, 5.0) == 0.0
    assert logarithmic_mean(-1.0, 5.0) == 0.0


def test_log_ratio_guards_non_positive() -> None:
    """log_ratio returns 0 when either argument is non-positive."""
    assert log_ratio(0.0, 2.0) == 0.0
    assert log_ratio(2.0, 0.0) == 0.0
    assert math.isclose(log_ratio(math.e, 1.0), 1.0)


def test_decomposition_delta_and_residual() -> None:
    """delta and residual derive from start/end and contributions."""
    decomp = Decomposition(
        country="A",
        start_year=2010,
        end_year=2020,
        target="co2",
        start_value=10.0,
        end_value=7.0,
        contributions={"x": -2.0, "y": -1.0},
    )
    assert decomp.delta == -3.0
    assert math.isclose(decomp.residual, 0.0)
