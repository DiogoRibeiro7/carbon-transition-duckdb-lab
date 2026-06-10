"""Uncertainty-aware scoring (v0.7).

Monte Carlo over weight perturbations: confidence bands for transition-risk
scores, rank-stability analysis, and top-k probabilities -- honest uncertainty
in place of a single point estimate.
"""

from __future__ import annotations

from carbon_transition_duckdb.uncertainty.montecarlo import (
    run_weight_samples,
    sample_weights,
    uncertainty_summary,
)

__all__ = ["run_weight_samples", "sample_weights", "uncertainty_summary"]
