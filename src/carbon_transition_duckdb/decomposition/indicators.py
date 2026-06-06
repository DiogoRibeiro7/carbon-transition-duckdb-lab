"""Transition indicators: electricity mix, fossil lock-in, industrial proxy.

These are transparent, derived indicators -- not causal claims. Each is a simple
function of mart columns over a start/end window, designed for screening and
comparison rather than attribution.
"""

from __future__ import annotations

from typing import cast

import pandas as pd

from carbon_transition_duckdb.decomposition.common import (
    resolve_year_bounds,
    two_year_rows,
)


def _annualised(start_value: float, end_value: float, years: int) -> float:
    """Average change per year between two values."""
    return (end_value - start_value) / years if years else 0.0


def transition_indicators(
    frame: pd.DataFrame,
    start_year: int | None = None,
    end_year: int | None = None,
    country_col: str = "country",
    year_col: str = "year",
) -> pd.DataFrame:
    """Compute per-country transition indicators over a start/end window.

    Columns returned per country:

    Electricity-mix transition
        ``renewables_share_elec_start`` / ``_end`` / ``_change`` and the annual
        change ``renewables_elec_annual``.

    Fossil lock-in
        ``fossil_share_start`` / ``_end``, the annual decline
        ``fossil_annual_decline`` (positive means falling), and a heuristic
        ``fossil_lockin_index`` -- high when the fossil share is large *and*
        falling slowly.

    Industrial proxy
        ``carbon_intensity_end`` and ``carbon_intensity_change`` -- the carbon
        content of energy is used as a transparent proxy for the carbon-heaviness
        of the energy/industrial mix (no industrial-output data is assumed).
    """
    required = {
        country_col,
        year_col,
        "renewables_share_elec",
        "fossil_share_energy",
        "carbon_intensity",
    }
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    low, high = resolve_year_bounds(frame, year_col, start_year, end_year)
    span = high - low

    records: list[dict[str, float | str]] = []
    for country in sorted(frame[country_col].dropna().unique()):
        rows = two_year_rows(
            frame[frame[country_col] == country], year_col, low, high
        )
        if rows is None:
            continue
        start, end = rows

        renew0 = float(start["renewables_share_elec"])
        renew1 = float(end["renewables_share_elec"])
        fossil0 = float(start["fossil_share_energy"])
        fossil1 = float(end["fossil_share_energy"])
        cint0 = float(start["carbon_intensity"])
        cint1 = float(end["carbon_intensity"])

        fossil_annual_decline = _annualised(fossil1, fossil0, span)  # positive = falling
        lockin = fossil1 / (1.0 + max(fossil_annual_decline, 0.0))

        records.append(
            {
                "country": str(country),
                "renewables_share_elec_start": round(renew0, 3),
                "renewables_share_elec_end": round(renew1, 3),
                "renewables_share_elec_change": round(renew1 - renew0, 3),
                "renewables_elec_annual": round(_annualised(renew0, renew1, span), 3),
                "fossil_share_start": round(fossil0, 3),
                "fossil_share_end": round(fossil1, 3),
                "fossil_annual_decline": round(fossil_annual_decline, 3),
                "fossil_lockin_index": round(lockin, 3),
                "carbon_intensity_end": round(cint1, 6),
                "carbon_intensity_change": round(cint1 - cint0, 6),
            }
        )

    out = pd.DataFrame.from_records(records)
    if not out.empty:
        out = out.sort_values("fossil_lockin_index", ascending=False).reset_index(
            drop=True
        )
    return cast(pd.DataFrame, out)
