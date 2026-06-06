"""Tests for country-group filters and flags."""

import pandas as pd
import pytest

from carbon_transition_duckdb.quality.country_groups import (
    EU27,
    OECD,
    add_group_flags,
    drop_aggregates,
    filter_by_group,
)


def _frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "country": ["Germany", "United States", "Brazil", "World"],
            "iso_code": ["DEU", "USA", "BRA", "OWID_WRL"],
            "co2": [1.0, 2.0, 3.0, 6.0],
        }
    )


def test_group_definitions_are_complete() -> None:
    """EU27 and OECD should have their canonical member counts."""
    assert len(EU27) == 27
    assert len(OECD) == 38


def test_filter_by_group_eu() -> None:
    """Filtering to the EU keeps only EU members by ISO3."""
    out = filter_by_group(_frame(), "eu")
    assert out["iso_code"].tolist() == ["DEU"]


def test_filter_by_group_explicit_codes() -> None:
    """An explicit ISO3 iterable should also work."""
    out = filter_by_group(_frame(), {"USA", "BRA"})
    assert set(out["iso_code"]) == {"USA", "BRA"}


def test_filter_by_group_unknown_raises() -> None:
    """An unknown named group should raise a clear error."""
    with pytest.raises(ValueError):
        filter_by_group(_frame(), "narnia")


def test_drop_aggregates() -> None:
    """Aggregate entities such as World should be removed by name."""
    out = drop_aggregates(_frame())
    assert "World" not in out["country"].tolist()
    assert len(out) == 3


def test_add_group_flags() -> None:
    """Membership flags should reflect EU/OECD by ISO3."""
    out = add_group_flags(_frame()).set_index("iso_code")
    assert bool(out.loc["DEU", "is_eu"]) is True
    assert bool(out.loc["USA", "is_eu"]) is False
    assert bool(out.loc["USA", "is_oecd"]) is True
