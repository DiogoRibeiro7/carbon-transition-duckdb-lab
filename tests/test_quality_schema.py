"""Tests for schema-drift validation."""

import pytest

from carbon_transition_duckdb.quality.schema import (
    RAW_CO2_SCHEMA,
    SchemaDriftError,
    assert_no_drift,
    validate_table_schema,
)


def test_validate_table_schema_detects_present_and_extra() -> None:
    """All required columns present plus an extra one should be valid."""
    actual = [*RAW_CO2_SCHEMA.required_columns, "gdp"]
    report = validate_table_schema(actual, RAW_CO2_SCHEMA)

    assert report.is_valid
    assert report.missing == ()
    assert "gdp" in report.extra


def test_validate_table_schema_detects_missing() -> None:
    """A dropped required column should be reported as drift."""
    actual = [c for c in RAW_CO2_SCHEMA.required_columns if c != "co2"]
    report = validate_table_schema(actual, RAW_CO2_SCHEMA)

    assert not report.is_valid
    assert "co2" in report.missing


def test_assert_no_drift_raises_on_missing() -> None:
    """assert_no_drift should raise SchemaDriftError when a column is missing."""
    report = validate_table_schema(["country"], RAW_CO2_SCHEMA)

    with pytest.raises(SchemaDriftError):
        assert_no_drift([report])


def test_assert_no_drift_passes_when_valid() -> None:
    """A valid report should not raise."""
    report = validate_table_schema(list(RAW_CO2_SCHEMA.required_columns), RAW_CO2_SCHEMA)
    assert_no_drift([report])  # should not raise
