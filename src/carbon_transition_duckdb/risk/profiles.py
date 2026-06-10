"""Configurable scoring profiles.

A scoring profile is a named, versioned set of component weights for the
transition-risk score. Profiles can be defined in code (the built-ins below) or
loaded from a YAML/JSON file, so the weighting is explicit and auditable rather
than hard-coded.

Example YAML profile::

    name: trend_focused
    description: Emphasise recent emissions trend and fossil dependence.
    weights:
      co2_trend: 0.40
      co2_per_capita: 0.15
      carbon_intensity: 0.15
      fossil_share: 0.20
      renewable_gap: 0.10
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from carbon_transition_duckdb.risk.scoring import ScoreWeights

_WEIGHT_FIELDS = (
    "co2_trend",
    "co2_per_capita",
    "carbon_intensity",
    "fossil_share",
    "renewable_gap",
)


@dataclass(frozen=True)
class ScoringProfile:
    """A named set of validated score weights."""

    name: str
    weights: ScoreWeights
    description: str = ""


def _weights_from_mapping(mapping: dict[str, Any]) -> ScoreWeights:
    """Build and validate ScoreWeights from a plain mapping."""
    unknown = set(mapping) - set(_WEIGHT_FIELDS)
    if unknown:
        raise ValueError(f"Unknown weight keys: {sorted(unknown)}")
    weights = ScoreWeights(**{key: float(mapping[key]) for key in mapping})
    weights.validate()
    return weights


def profile_from_dict(data: dict[str, Any]) -> ScoringProfile:
    """Build a :class:`ScoringProfile` from a parsed mapping."""
    if "weights" not in data:
        raise ValueError("Profile is missing a 'weights' section.")
    return ScoringProfile(
        name=str(data.get("name", "custom")),
        description=str(data.get("description", "")),
        weights=_weights_from_mapping(dict(data["weights"])),
    )


def load_profile(path: Path) -> ScoringProfile:
    """Load a scoring profile from a YAML (.yaml/.yml) or JSON (.json) file."""
    if not path.exists():
        raise FileNotFoundError(f"Profile file not found: {path}")
    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        import yaml  # lazy import; pyyaml is a declared dependency

        data = yaml.safe_load(text)
    elif suffix == ".json":
        data = json.loads(text)
    else:
        raise ValueError(f"Unsupported profile format: {suffix!r} (use .yaml or .json).")
    if not isinstance(data, dict):
        raise ValueError("Profile file must contain a mapping at the top level.")
    return profile_from_dict(data)


BUILTIN_PROFILES: dict[str, ScoringProfile] = {
    "default": ScoringProfile(
        name="default",
        description="Balanced v0.1 weights.",
        weights=ScoreWeights(),
    ),
    "trend_focused": ScoringProfile(
        name="trend_focused",
        description="Emphasise recent emissions trend and fossil dependence.",
        weights=ScoreWeights(
            co2_trend=0.40,
            co2_per_capita=0.15,
            carbon_intensity=0.15,
            fossil_share=0.20,
            renewable_gap=0.10,
        ),
    ),
    "renewables_focused": ScoringProfile(
        name="renewables_focused",
        description="Emphasise renewable electricity gap and fossil share.",
        weights=ScoreWeights(
            co2_trend=0.20,
            co2_per_capita=0.15,
            carbon_intensity=0.15,
            fossil_share=0.20,
            renewable_gap=0.30,
        ),
    ),
}


def get_profile(name_or_path: str) -> ScoringProfile:
    """Resolve a profile by built-in name or by file path."""
    if name_or_path in BUILTIN_PROFILES:
        return BUILTIN_PROFILES[name_or_path]
    return load_profile(Path(name_or_path))
