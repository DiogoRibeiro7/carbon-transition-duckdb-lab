"""Kaya identity decomposition of CO2 emissions change.

The Kaya identity expresses CO2 emissions as a product of factors. With GDP
available (real OWID data) the four-factor form is used::

    CO2 = Population
         * (GDP / Population)              # affluence
         * (Energy / GDP)                  # energy intensity of GDP
         * (CO2 / Energy)                  # carbon intensity of energy

Without GDP (e.g. the synthetic data) a three-factor form is used::

    CO2 = Population
         * (Energy / Population)           # energy use per capita
         * (CO2 / Energy)                  # carbon intensity of energy

The change in CO2 between two years is split into additive per-factor
contributions with LMDI, so the contributions sum exactly to the total change.
"""

from __future__ import annotations

from typing import cast

import pandas as pd

from carbon_transition_duckdb.decomposition.common import (
    resolve_year_bounds,
    two_year_rows,
)
from carbon_transition_duckdb.decomposition.lmdi import (
    Decomposition,
    log_ratio,
    logarithmic_mean,
)

_REQUIRED = ("country", "year", "population", "co2", "primary_energy_consumption")


def _has_gdp(frame: pd.DataFrame, start: pd.Series, end: pd.Series) -> bool:
    """Return True when a usable positive GDP value exists at both endpoints."""
    if "gdp" not in frame.columns:
        return False
    g0, g1 = start.get("gdp"), end.get("gdp")
    return bool(pd.notna(g0) and pd.notna(g1) and float(g0) > 0 and float(g1) > 0)


def kaya_decomposition(
    frame: pd.DataFrame,
    country: str,
    start_year: int,
    end_year: int,
    country_col: str = "country",
    year_col: str = "year",
) -> Decomposition:
    """Decompose one country's CO2 change between two years via the Kaya identity."""
    missing = {country_col, year_col, "population", "co2", "primary_energy_consumption"}
    missing -= set(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    rows = two_year_rows(frame[frame[country_col] == country], year_col, start_year, end_year)
    if rows is None:
        raise ValueError(
            f"{country!r} is missing data for {start_year} and/or {end_year}."
        )
    start, end = rows

    pop0, pop1 = float(start["population"]), float(end["population"])
    co20, co21 = float(start["co2"]), float(end["co2"])
    en0, en1 = (
        float(start["primary_energy_consumption"]),
        float(end["primary_energy_consumption"]),
    )

    weight = logarithmic_mean(co21, co20)
    contributions: dict[str, float] = {
        "population": weight * log_ratio(pop1, pop0),
    }

    if _has_gdp(frame, start, end):
        gdp0, gdp1 = float(start["gdp"]), float(end["gdp"])
        contributions["affluence"] = weight * log_ratio(gdp1 / pop1, gdp0 / pop0)
        contributions["energy_intensity"] = weight * log_ratio(en1 / gdp1, en0 / gdp0)
    else:
        contributions["energy_per_capita"] = weight * log_ratio(en1 / pop1, en0 / pop0)

    contributions["carbon_intensity"] = weight * log_ratio(co21 / en1, co20 / en0)

    return Decomposition(
        country=country,
        start_year=start_year,
        end_year=end_year,
        target="co2",
        start_value=co20,
        end_value=co21,
        contributions=contributions,
    )


def kaya_decomposition_frame(
    frame: pd.DataFrame,
    start_year: int | None = None,
    end_year: int | None = None,
    country_col: str = "country",
    year_col: str = "year",
) -> pd.DataFrame:
    """Run the Kaya decomposition for every country with both endpoints.

    Returns one row per country with the start/end CO2, total change, each factor
    contribution, and the (near-zero) residual.
    """
    low, high = resolve_year_bounds(frame, year_col, start_year, end_year)

    records: list[dict[str, float | str]] = []
    for country in sorted(frame[country_col].dropna().unique()):
        country_frame = frame[frame[country_col] == country]
        if two_year_rows(country_frame, year_col, low, high) is None:
            continue
        result = kaya_decomposition(
            frame, str(country), low, high, country_col=country_col, year_col=year_col
        )
        record: dict[str, float | str] = {
            "country": result.country,
            "co2_start": round(result.start_value, 4),
            "co2_end": round(result.end_value, 4),
            "delta_co2": round(result.delta, 4),
        }
        for factor, value in result.contributions.items():
            record[f"{factor}_effect"] = round(value, 4)
        record["residual"] = round(result.residual, 6)
        records.append(record)

    return cast(pd.DataFrame, pd.DataFrame.from_records(records))
