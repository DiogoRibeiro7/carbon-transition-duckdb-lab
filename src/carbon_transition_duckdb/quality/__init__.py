"""Data-quality and validation utilities (v0.2).

This subpackage groups the transparent data-quality checks that protect the
analytical layer: schema-drift detection, missingness reporting, country/entity
normalization, country-group filters, and reproducible data manifests.
"""

from __future__ import annotations

from carbon_transition_duckdb.quality.country_groups import (
    AGGREGATE_ENTITIES,
    EU27,
    INCOME_GROUPS_SAMPLE,
    OECD,
    add_group_flags,
    filter_by_group,
)
from carbon_transition_duckdb.quality.manifest import (
    FileChecksum,
    build_manifest,
    verify_manifest,
    write_manifest,
)
from carbon_transition_duckdb.quality.missingness import (
    METRIC_COLUMNS,
    missingness_by_country,
    missingness_by_metric,
    write_missingness_report,
)
from carbon_transition_duckdb.quality.normalization import (
    COUNTRY_ALIASES,
    normalize_country_column,
    normalize_country_name,
)
from carbon_transition_duckdb.quality.schema import (
    RAW_CO2_SCHEMA,
    RAW_ENERGY_SCHEMA,
    SchemaDriftError,
    SchemaReport,
    TableSchema,
    assert_no_drift,
    validate_connection_schemas,
    validate_table_schema,
)

__all__ = [
    "AGGREGATE_ENTITIES",
    "COUNTRY_ALIASES",
    "EU27",
    "INCOME_GROUPS_SAMPLE",
    "METRIC_COLUMNS",
    "OECD",
    "RAW_CO2_SCHEMA",
    "RAW_ENERGY_SCHEMA",
    "FileChecksum",
    "SchemaDriftError",
    "SchemaReport",
    "TableSchema",
    "add_group_flags",
    "assert_no_drift",
    "build_manifest",
    "filter_by_group",
    "missingness_by_country",
    "missingness_by_metric",
    "normalize_country_column",
    "normalize_country_name",
    "validate_connection_schemas",
    "validate_table_schema",
    "verify_manifest",
    "write_manifest",
    "write_missingness_report",
]
