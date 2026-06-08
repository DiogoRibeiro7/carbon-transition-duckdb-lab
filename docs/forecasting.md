# Forecasting & Scenarios (v0.4)

The `carbon_transition_duckdb.forecasting` subpackage provides transparent
baseline projections. They assume the recent linear trend continues and make no
causal or policy claims -- they are screening tools, not calibrated forecasts.

## Baseline trend forecasts

`trend.py` fits an ordinary-least-squares line to each country's history and
extrapolates it. Uncertainty is an approximate prediction interval using the
standard error of an individual prediction:

```text
se = s * sqrt(1 + 1/n + (year - x_mean)^2 / Sxx)
interval = forecast ± z * se        (z = 1.96 for ~95%)
```

The interval widens as the projection moves away from the observed data.

```python
from carbon_transition_duckdb.forecasting import forecast_frame, trend_table
trend_table(mart, "co2")
forecast_frame(mart, "co2", horizon=6)
```

## Scenario comparison

`scenarios.py` projects a metric forward under constant annual-rate assumptions
anchored to a business-as-usual rate (the historical CAGR):

```python
from carbon_transition_duckdb.forecasting import (
    default_scenarios, historical_cagr, scenario_comparison,
)
bau = historical_cagr(mart, "Borealia", "co2")
scenario_comparison(mart, "Borealia", "co2", default_scenarios(bau), horizon=10)
```

`default_scenarios` returns `business_as_usual`, `flat`, `reduce_2pct`, and
`reduce_5pct`. Any `{name: annual_rate}` mapping can be supplied instead.

## Policy target gap analysis

`targets.py` expresses a target as "cut <metric> by <reduction> relative to its
<base_year> level by <target_year>", projects the metric to the target year with
the baseline trend, and reports the gap:

```python
from carbon_transition_duckdb.forecasting import ReductionTarget, target_gap_frame
target = ReductionTarget(metric="co2", base_year=2010, target_year=2030, reduction=0.30)
target_gap_frame(mart, target)
```

`on_track` is True when the projection meets or beats the target level.

## CLI

```bash
poetry run carbon-duckdb forecast --metric co2 --horizon 6
poetry run carbon-duckdb target-gap --metric co2 --base-year 2010 --target-year 2030 --reduction 0.30
```

See `notebooks/07_forecasting_scenarios.ipynb` for a runnable, charted tour.
