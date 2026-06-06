"""Country and entity name normalization.

Public datasets and downstream joins use inconsistent country labels
("USA" vs "United States", "Czech Republic" vs "Czechia"). This module maps
common aliases onto a canonical name so joins and group membership stay stable.

The alias table is intentionally small and curated. It is not a complete country
database; it covers the labels that most often differ between sources.
"""

from __future__ import annotations

from typing import cast

import pandas as pd

# Keys are compared case-insensitively after stripping surrounding whitespace.
COUNTRY_ALIASES: dict[str, str] = {
    "usa": "United States",
    "u.s.": "United States",
    "u.s.a.": "United States",
    "united states of america": "United States",
    "uk": "United Kingdom",
    "u.k.": "United Kingdom",
    "great britain": "United Kingdom",
    "britain": "United Kingdom",
    "czech republic": "Czechia",
    "south korea": "South Korea",
    "korea, rep.": "South Korea",
    "republic of korea": "South Korea",
    "north korea": "North Korea",
    "korea, dem. people's rep.": "North Korea",
    "russia": "Russia",
    "russian federation": "Russia",
    "iran, islamic rep.": "Iran",
    "islamic republic of iran": "Iran",
    "egypt, arab rep.": "Egypt",
    "syrian arab republic": "Syria",
    "viet nam": "Vietnam",
    "lao pdr": "Laos",
    "brunei darussalam": "Brunei",
    "cote d'ivoire": "Cote d'Ivoire",
    "côte d'ivoire": "Cote d'Ivoire",
    "ivory coast": "Cote d'Ivoire",
    "turkiye": "Turkey",
    "türkiye": "Turkey",
    "macedonia": "North Macedonia",
    "swaziland": "Eswatini",
    "cape verde": "Cabo Verde",
    "democratic republic of congo": "Democratic Republic of Congo",
    "congo, dem. rep.": "Democratic Republic of Congo",
    "congo, rep.": "Congo",
}


def normalize_country_name(name: str) -> str:
    """Return the canonical name for a country label.

    Unknown labels are returned stripped but otherwise unchanged, so the
    function is safe to apply to an entire column.
    """
    stripped = name.strip()
    return COUNTRY_ALIASES.get(stripped.lower(), stripped)


def normalize_country_column(
    frame: pd.DataFrame, column: str = "country"
) -> pd.DataFrame:
    """Return a copy of ``frame`` with a normalized country column."""
    if column not in frame.columns:
        raise ValueError(f"Column {column!r} is required.")
    out = frame.copy()
    out[column] = out[column].astype("string").map(
        lambda value: normalize_country_name(value) if pd.notna(value) else value
    )
    return cast(pd.DataFrame, out)
