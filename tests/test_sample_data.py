"""Tests for synthetic data generation."""

from pathlib import Path

import pandas as pd

from carbon_transition_duckdb.sample_data import generate_synthetic_owid_data


def test_generate_synthetic_owid_data(tmp_path: Path) -> None:
    """Synthetic generator should create two non-empty CSV files."""
    co2_path, energy_path = generate_synthetic_owid_data(
        output_dir=tmp_path,
        start_year=2020,
        end_year=2021,
        seed=7,
    )

    assert co2_path.exists()
    assert energy_path.exists()

    co2 = pd.read_csv(co2_path)
    energy = pd.read_csv(energy_path)

    assert not co2.empty
    assert not energy.empty
    assert {"country", "year", "co2", "co2_per_capita"}.issubset(co2.columns)
    assert {"country", "year", "fossil_share_energy", "renewables_share_elec"}.issubset(
        energy.columns
    )


def test_generate_synthetic_owid_data_rejects_bad_years(tmp_path: Path) -> None:
    """The generator should reject an invalid year interval."""
    try:
        generate_synthetic_owid_data(output_dir=tmp_path, start_year=2025, end_year=2020)
    except ValueError as exc:
        assert "start_year" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid year interval.")
