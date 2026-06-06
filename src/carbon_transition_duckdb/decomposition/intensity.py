"""Emissions-intensity decomposition.

Decomposes the change in CO2 *per capita* into two LMDI factors::

    CO2 / Population = (Energy / Population)   # energy use per capita
                     * (CO2 / Energy)          # carbon intensity of energy

This isolates how much of a country's per-capita emissions change came from
using more/less energy per person versus cleaning up the energy it uses.
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


def intensity_decomposition(
    frame: pd.DataFrame,
    country: str,
    start_year: int,
    end_year: int,
    country_col: str = "country",
    year_col: str = "year",
) -> Decomposition:
    """Decompose one country's CO2-per-capita change between two years."""
    required = {country_col, year_col, "population", "co2", "primary_energy_consumption"}
    missing = required - set(frame.columns)
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

    cpc0 = co20 / pop0 if pop0 else 0.0
    cpc1 = co21 / pop1 if pop1 else 0.0
    weight = logarithmic_mean(cpc1, cpc0)

    contributions = {
        "energy_per_capita": weight * log_ratio(en1 / pop1, en0 / pop0),
        "carbon_intensity": weight * log_ratio(co21 / en1, co20 / en0),
    }

    return Decomposition(
        country=country,
        start_year=start_year,
        end_year=end_year,
        target="co2_per_capita",
        start_value=cpc0,
        end_value=cpc1,
        contributions=contributions,
    )


def intensity_decomposition_frame(
    frame: pd.DataFrame,
    start_year: int | None = None,
    end_year: int | None = None,
    country_col: str = "country",
    year_col: str = "year",
) -> pd.DataFrame:
    """Run the per-capita intensity decomposition for every eligible country."""
    low, high = resolve_year_bounds(frame, year_col, start_year, end_year)

    records: list[dict[str, float | str]] = []
    for country in sorted(frame[country_col].dropna().unique()):
        country_frame = frame[frame[country_col] == country]
        if two_year_rows(country_frame, year_col, low, high) is None:
            continue
        result = intensity_decomposition(
            frame, str(country), low, high, country_col=country_col, year_col=year_col
        )
        records.append(
            {
                "country": result.country,
                "co2_per_capita_start": round(result.start_value, 4),
                "co2_per_capita_end": round(result.end_value, 4),
                "delta": round(result.delta, 4),
                "energy_per_capita_effect": round(
                    result.contributions["energy_per_capita"], 4
                ),
                "carbon_intensity_effect": round(
                    result.contributions["carbon_intensity"], 4
                ),
                "residual": round(result.residual, 6),
            }
        )

    return cast(pd.DataFrame, pd.DataFrame.from_records(records))
