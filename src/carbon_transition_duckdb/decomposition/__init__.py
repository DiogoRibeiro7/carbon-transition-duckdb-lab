"""Decomposition and attribution utilities (v0.3).

Transparent, additive decompositions and derived transition indicators:

- Kaya identity decomposition of CO2 change (LMDI, 3- or 4-factor).
- Emissions-intensity decomposition of CO2-per-capita change.
- Electricity-mix, fossil lock-in, and industrial-proxy indicators.
"""

from __future__ import annotations

from carbon_transition_duckdb.decomposition.indicators import transition_indicators
from carbon_transition_duckdb.decomposition.intensity import (
    intensity_decomposition,
    intensity_decomposition_frame,
)
from carbon_transition_duckdb.decomposition.kaya import (
    kaya_decomposition,
    kaya_decomposition_frame,
)
from carbon_transition_duckdb.decomposition.lmdi import (
    Decomposition,
    log_ratio,
    logarithmic_mean,
)

__all__ = [
    "Decomposition",
    "intensity_decomposition",
    "intensity_decomposition_frame",
    "kaya_decomposition",
    "kaya_decomposition_frame",
    "log_ratio",
    "logarithmic_mean",
    "transition_indicators",
]
