"""Tests for country-name normalization."""

import pandas as pd

from carbon_transition_duckdb.quality.normalization import (
    normalize_country_column,
    normalize_country_name,
)


def test_normalize_country_name_known_aliases() -> None:
    """Common aliases should map to canonical names, case-insensitively."""
    assert normalize_country_name("USA") == "United States"
    assert normalize_country_name("  czech republic ") == "Czechia"
    assert normalize_country_name("Russian Federation") == "Russia"


def test_normalize_country_name_unknown_is_passthrough() -> None:
    """Unknown labels are returned stripped but unchanged."""
    assert normalize_country_name("  Atlantis ") == "Atlantis"


def test_normalize_country_column() -> None:
    """Column normalization should rewrite recognised aliases."""
    frame = pd.DataFrame({"country": ["USA", "Atlantis", "UK"]})
    out = normalize_country_column(frame)

    assert out["country"].tolist() == ["United States", "Atlantis", "United Kingdom"]
    # original frame is untouched
    assert frame["country"].tolist() == ["USA", "Atlantis", "UK"]
