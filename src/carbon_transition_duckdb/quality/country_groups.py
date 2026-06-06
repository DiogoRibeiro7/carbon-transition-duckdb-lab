"""Country-group definitions and filters.

Analyses frequently need to restrict to, or flag, a peer group: drop aggregate
entities such as *World*, or keep only the EU, the OECD, or an income tier.
Groups are defined by ISO 3166-1 alpha-3 code so they survive name differences.

``EU27`` and ``OECD`` are complete. ``INCOME_GROUPS_SAMPLE`` is a small,
illustrative subset of the World Bank income classification; supply a fuller
mapping for production use.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import cast

import pandas as pd

# Aggregate / non-country entities that OWID mixes into the country column.
AGGREGATE_ENTITIES: frozenset[str] = frozenset(
    {
        "World",
        "Africa",
        "Asia",
        "Europe",
        "European Union (27)",
        "North America",
        "South America",
        "Oceania",
        "High-income countries",
        "Upper-middle-income countries",
        "Lower-middle-income countries",
        "Low-income countries",
    }
)

# EU member states (27) as ISO3.
EU27: frozenset[str] = frozenset(
    {
        "AUT", "BEL", "BGR", "HRV", "CYP", "CZE", "DNK", "EST", "FIN", "FRA",
        "DEU", "GRC", "HUN", "IRL", "ITA", "LVA", "LTU", "LUX", "MLT", "NLD",
        "POL", "PRT", "ROU", "SVK", "SVN", "ESP", "SWE",
    }
)

# OECD member states (38) as ISO3.
OECD: frozenset[str] = frozenset(
    {
        "AUS", "AUT", "BEL", "CAN", "CHL", "COL", "CRI", "CZE", "DNK", "EST",
        "FIN", "FRA", "DEU", "GRC", "HUN", "ISL", "IRL", "ISR", "ITA", "JPN",
        "KOR", "LVA", "LTU", "LUX", "MEX", "NLD", "NZL", "NOR", "POL", "PRT",
        "SVK", "SVN", "ESP", "SWE", "CHE", "TUR", "GBR", "USA",
    }
)

# Illustrative World Bank income tiers (NOT exhaustive).
INCOME_GROUPS_SAMPLE: dict[str, frozenset[str]] = {
    "high": frozenset({"USA", "DEU", "JPN", "GBR", "FRA", "CAN", "AUS", "KOR"}),
    "upper_middle": frozenset({"CHN", "BRA", "ZAF", "MEX", "RUS", "TUR", "ARG"}),
    "lower_middle": frozenset({"IND", "IDN", "NGA", "EGY", "PAK", "VNM", "PHL"}),
    "low": frozenset({"ETH", "COD", "AFG", "MOZ", "UGA", "MLI", "NER"}),
}

# Named groups that can be referenced by string in :func:`filter_by_group`.
NAMED_GROUPS: dict[str, frozenset[str]] = {
    "eu": EU27,
    "eu27": EU27,
    "oecd": OECD,
}


def _resolve_group(group: str | Iterable[str]) -> frozenset[str]:
    """Resolve a group name or an explicit ISO3 collection to a code set."""
    if isinstance(group, str):
        key = group.strip().lower()
        if key in NAMED_GROUPS:
            return NAMED_GROUPS[key]
        if key in INCOME_GROUPS_SAMPLE:
            return INCOME_GROUPS_SAMPLE[key]
        raise ValueError(
            f"Unknown group {group!r}. Known groups: "
            f"{sorted(set(NAMED_GROUPS) | set(INCOME_GROUPS_SAMPLE))}."
        )
    return frozenset(group)


def filter_by_group(
    frame: pd.DataFrame,
    group: str | Iterable[str],
    iso_col: str = "iso_code",
) -> pd.DataFrame:
    """Keep only rows whose ISO3 code belongs to ``group``.

    ``group`` may be a known name ("eu", "oecd", an income tier) or any
    iterable of ISO3 codes.
    """
    if iso_col not in frame.columns:
        raise ValueError(f"Column {iso_col!r} is required.")
    codes = _resolve_group(group)
    return cast(pd.DataFrame, frame.loc[frame[iso_col].isin(codes)].copy())


def drop_aggregates(
    frame: pd.DataFrame,
    country_col: str = "country",
    aggregates: Iterable[str] = AGGREGATE_ENTITIES,
) -> pd.DataFrame:
    """Drop aggregate / non-country entities from a frame."""
    if country_col not in frame.columns:
        raise ValueError(f"Column {country_col!r} is required.")
    excluded = set(aggregates)
    return cast(pd.DataFrame, frame.loc[~frame[country_col].isin(excluded)].copy())


def add_group_flags(frame: pd.DataFrame, iso_col: str = "iso_code") -> pd.DataFrame:
    """Add boolean ``is_eu`` / ``is_oecd`` membership columns by ISO3 code."""
    if iso_col not in frame.columns:
        raise ValueError(f"Column {iso_col!r} is required.")
    out = frame.copy()
    out["is_eu"] = out[iso_col].isin(EU27)
    out["is_oecd"] = out[iso_col].isin(OECD)
    return cast(pd.DataFrame, out)
