"""Tests for OLS trend forecasts."""

import math

import pandas as pd
import pytest

from carbon_transition_duckdb.forecasting.trend import (
    fit_linear_trend,
    forecast_metric,
    trend_table,
)


def test_fit_linear_trend_recovers_known_line() -> None:
    """A perfect line should be recovered exactly with R^2 == 1."""
    years = [2000, 2001, 2002, 2003, 2004]
    values = [10.0 + 2.0 * (y - 2000) for y in years]
    trend = fit_linear_trend(years, values)

    assert math.isclose(trend.slope, 2.0, abs_tol=1e-9)
    assert math.isclose(trend.intercept, 10.0 - 2.0 * 2000, abs_tol=1e-6)
    assert math.isclose(trend.r_squared, 1.0, abs_tol=1e-9)
    assert math.isclose(trend.predict(2005), 20.0, abs_tol=1e-6)


def test_predict_interval_brackets_point() -> None:
    """The prediction interval should contain the point forecast and widen."""
    years = [2000, 2001, 2002, 2003, 2004]
    values = [1.0, 2.1, 2.9, 4.2, 4.8]
    trend = fit_linear_trend(years, values)

    point, lower, upper = trend.predict_interval(2006)
    assert lower < point < upper
    # Further extrapolation is at least as uncertain as a nearer one.
    width_near = trend.predict_interval(2005)[2] - trend.predict_interval(2005)[1]
    width_far = upper - lower
    assert width_far >= width_near


def test_fit_requires_min_observations() -> None:
    """Fewer than min_obs points should raise."""
    with pytest.raises(ValueError):
        fit_linear_trend([2000, 2001], [1.0, 2.0])


def test_forecast_metric_horizon_and_columns() -> None:
    """forecast_metric returns horizon rows past the last year."""
    frame = pd.DataFrame(
        {
            "country": ["A"] * 5,
            "year": [2010, 2011, 2012, 2013, 2014],
            "co2": [10.0, 9.5, 9.0, 8.4, 8.1],
        }
    )
    out = forecast_metric(frame, "A", "co2", horizon=3)

    assert list(out["year"]) == [2015, 2016, 2017]
    assert {"forecast", "lower", "upper"}.issubset(out.columns)
    assert (out["lower"] <= out["forecast"]).all()
    assert (out["forecast"] <= out["upper"]).all()


def test_trend_table_reports_annual_change() -> None:
    """trend_table reports a negative slope for a declining series."""
    frame = pd.DataFrame(
        {
            "country": ["A"] * 4,
            "year": [2010, 2011, 2012, 2013],
            "co2": [10.0, 9.0, 8.0, 7.0],
        }
    )
    table = trend_table(frame, "co2").set_index("country")
    assert math.isclose(table.loc["A", "annual_change"], -1.0, abs_tol=1e-6)
