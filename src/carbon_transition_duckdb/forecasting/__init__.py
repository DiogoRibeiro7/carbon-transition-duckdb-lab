"""Forecasting and scenario utilities (v0.4).

Transparent, baseline projections:

- OLS trend forecasts with approximate prediction intervals.
- Constant-rate scenario comparison tables.
- Policy target gap analysis against a trend projection.
"""

from __future__ import annotations

from carbon_transition_duckdb.forecasting.scenarios import (
    default_scenarios,
    historical_cagr,
    project_constant_growth,
    scenario_comparison,
)
from carbon_transition_duckdb.forecasting.targets import (
    ReductionTarget,
    TargetGap,
    target_gap,
    target_gap_frame,
)
from carbon_transition_duckdb.forecasting.trend import (
    LinearTrend,
    fit_linear_trend,
    forecast_frame,
    forecast_metric,
    trend_table,
)

__all__ = [
    "LinearTrend",
    "ReductionTarget",
    "TargetGap",
    "default_scenarios",
    "fit_linear_trend",
    "forecast_frame",
    "forecast_metric",
    "historical_cagr",
    "project_constant_growth",
    "scenario_comparison",
    "target_gap",
    "target_gap_frame",
    "trend_table",
]
