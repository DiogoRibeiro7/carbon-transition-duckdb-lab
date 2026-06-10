"""Tests for configurable scoring profiles."""

import json
from pathlib import Path

import pytest

from carbon_transition_duckdb.risk.profiles import (
    BUILTIN_PROFILES,
    get_profile,
    load_profile,
    profile_from_dict,
)

_VALID = {
    "name": "custom",
    "description": "test",
    "weights": {
        "co2_trend": 0.30,
        "co2_per_capita": 0.20,
        "carbon_intensity": 0.20,
        "fossil_share": 0.20,
        "renewable_gap": 0.10,
    },
}


def test_builtin_profiles_are_valid() -> None:
    """Every built-in profile must have weights summing to 1."""
    assert {"default", "trend_focused", "renewables_focused"} <= set(BUILTIN_PROFILES)
    for profile in BUILTIN_PROFILES.values():
        profile.weights.validate()  # should not raise


def test_profile_from_dict() -> None:
    """A valid mapping builds a profile with the expected weights."""
    profile = profile_from_dict(_VALID)
    assert profile.name == "custom"
    assert profile.weights.co2_trend == 0.30


def test_profile_rejects_unknown_weight_keys() -> None:
    """Unknown weight keys should raise."""
    bad = {"weights": {**_VALID["weights"], "mystery": 0.0}}
    with pytest.raises(ValueError):
        profile_from_dict(bad)


def test_profile_rejects_unnormalised_weights() -> None:
    """Weights that do not sum to 1 should raise."""
    bad = {"weights": {**_VALID["weights"], "co2_trend": 0.99}}
    with pytest.raises(ValueError):
        profile_from_dict(bad)


def test_load_profile_yaml(tmp_path: Path) -> None:
    """A YAML profile loads and validates."""
    path = tmp_path / "p.yaml"
    path.write_text(
        "name: y\nweights:\n"
        "  co2_trend: 0.2\n  co2_per_capita: 0.2\n  carbon_intensity: 0.2\n"
        "  fossil_share: 0.2\n  renewable_gap: 0.2\n",
        encoding="utf-8",
    )
    profile = load_profile(path)
    assert profile.name == "y"
    assert profile.weights.renewable_gap == 0.2


def test_load_profile_json(tmp_path: Path) -> None:
    """A JSON profile loads and validates."""
    path = tmp_path / "p.json"
    path.write_text(json.dumps(_VALID), encoding="utf-8")
    assert load_profile(path).weights.co2_per_capita == 0.20


def test_get_profile_resolves_builtin_and_path(tmp_path: Path) -> None:
    """get_profile resolves a built-in name and a file path."""
    assert get_profile("default").name == "default"
    path = tmp_path / "p.json"
    path.write_text(json.dumps(_VALID), encoding="utf-8")
    assert get_profile(str(path)).name == "custom"


def test_load_profile_unsupported_format(tmp_path: Path) -> None:
    """An unsupported extension raises a clear error."""
    path = tmp_path / "p.txt"
    path.write_text("nope", encoding="utf-8")
    with pytest.raises(ValueError):
        load_profile(path)
