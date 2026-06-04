"""Synthetic OWID-like data generation.

The sample generator produces small files with the same spirit as the public
OWID CO2 and energy datasets. It is intentionally small and deterministic so
tests and examples do not depend on network access.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class SyntheticCountry:
    """Base parameters for a synthetic country."""

    country: str
    iso_code: str
    base_population: float
    base_co2: float
    base_energy: float
    fossil_share: float
    renewable_share: float
    transition_speed: float


DEFAULT_COUNTRIES: tuple[SyntheticCountry, ...] = (
    SyntheticCountry("Atlantis", "ATL", 8_000_000, 60.0, 320.0, 76.0, 18.0, 1.4),
    SyntheticCountry("Borealia", "BOR", 18_000_000, 170.0, 880.0, 83.0, 12.0, 0.7),
    SyntheticCountry("Cyrenia", "CYR", 4_500_000, 18.0, 120.0, 44.0, 42.0, 2.1),
    SyntheticCountry("Deltora", "DEL", 31_000_000, 250.0, 1_420.0, 88.0, 8.0, 0.3),
    SyntheticCountry("Estavia", "EST", 12_000_000, 42.0, 260.0, 52.0, 36.0, 1.9),
)


def _bounded(value: float, lower: float, upper: float) -> float:
    """Clamp a value to a closed interval."""
    return max(lower, min(upper, value))


def generate_synthetic_owid_data(
    output_dir: Path,
    start_year: int = 2010,
    end_year: int = 2024,
    seed: int = 42,
) -> tuple[Path, Path]:
    """Generate synthetic CO2 and energy CSV files.

    Parameters
    ----------
    output_dir:
        Directory where the two CSV files will be written.
    start_year:
        First year in the generated data.
    end_year:
        Last year in the generated data.
    seed:
        Random seed for reproducibility.

    Returns
    -------
    tuple[Path, Path]
        Paths to the generated CO2 and energy CSV files.
    """
    if start_year > end_year:
        raise ValueError("start_year must be lower than or equal to end_year.")

    rng = random.Random(seed)
    output_dir.mkdir(parents=True, exist_ok=True)

    co2_rows: list[dict[str, float | int | str]] = []
    energy_rows: list[dict[str, float | int | str]] = []

    for country in DEFAULT_COUNTRIES:
        for year in range(start_year, end_year + 1):
            t = year - start_year
            population = country.base_population * (1.0 + 0.009 * t)
            renewable_share = _bounded(
                country.renewable_share + country.transition_speed * t + rng.uniform(-1.0, 1.0),
                0.0,
                95.0,
            )
            fossil_share = _bounded(
                country.fossil_share - 0.8 * country.transition_speed * t + rng.uniform(-1.2, 1.2),
                2.0,
                98.0,
            )
            primary_energy = country.base_energy * (1.0 + 0.012 * t + rng.uniform(-0.015, 0.015))
            intensity = (fossil_share / 100.0) * rng.uniform(0.16, 0.25)
            co2 = country.base_co2 * (1.0 + 0.005 * t) * (fossil_share / country.fossil_share)
            co2 *= rng.uniform(0.95, 1.05)
            electricity_generation = primary_energy * rng.uniform(0.25, 0.38)

            co2_rows.append(
                {
                    "country": country.country,
                    "iso_code": country.iso_code,
                    "year": year,
                    "population": round(population),
                    "co2": round(co2, 4),
                    "co2_per_capita": round(co2 * 1_000_000 / population, 4),
                    "energy_per_capita": round(primary_energy * 1_000_000 / population, 4),
                    "carbon_intensity": round(intensity, 6),
                }
            )
            energy_rows.append(
                {
                    "country": country.country,
                    "iso_code": country.iso_code,
                    "year": year,
                    "primary_energy_consumption": round(primary_energy, 4),
                    "fossil_share_energy": round(fossil_share, 4),
                    "renewables_share_energy": round(renewable_share, 4),
                    "renewables_share_elec": round(
                        _bounded(renewable_share + rng.uniform(-3, 4), 0, 98), 4
                    ),
                    "electricity_generation": round(electricity_generation, 4),
                }
            )

    co2_path = output_dir / "owid-co2-data.csv"
    energy_path = output_dir / "owid-energy-data.csv"

    pd.DataFrame(co2_rows).to_csv(co2_path, index=False)
    pd.DataFrame(energy_rows).to_csv(energy_path, index=False)

    return co2_path, energy_path
