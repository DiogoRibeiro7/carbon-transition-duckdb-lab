"""Schema validation to detect OWID column drift.

Public datasets evolve: columns get renamed, added, or removed. The pipeline
only depends on a small, named subset of columns, so this module checks that the
*required* columns are present and reports any drift explicitly instead of
failing deep inside a SQL transform.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TableSchema:
    """The columns a downstream transform depends on for one table."""

    name: str
    required_columns: tuple[str, ...]


@dataclass(frozen=True)
class SchemaReport:
    """Result of validating a table against a :class:`TableSchema`."""

    table: str
    present: tuple[str, ...]
    missing: tuple[str, ...]
    extra: tuple[str, ...]

    @property
    def is_valid(self) -> bool:
        """A schema is valid when no required column is missing."""
        return not self.missing


class SchemaDriftError(RuntimeError):
    """Raised when one or more required columns are missing."""


# Required columns are the subset the country-year mart actually reads. Real OWID
# files carry many more columns; extra columns are reported but never an error.
RAW_CO2_SCHEMA = TableSchema(
    name="raw_owid_co2",
    required_columns=(
        "country",
        "iso_code",
        "year",
        "population",
        "co2",
        "co2_per_capita",
    ),
)

RAW_ENERGY_SCHEMA = TableSchema(
    name="raw_owid_energy",
    required_columns=(
        "country",
        "year",
        "primary_energy_consumption",
        "fossil_share_energy",
        "renewables_share_energy",
        "renewables_share_elec",
        "electricity_generation",
    ),
)

DEFAULT_RAW_SCHEMAS: tuple[TableSchema, ...] = (RAW_CO2_SCHEMA, RAW_ENERGY_SCHEMA)


def table_columns(connection: Any, table: str) -> list[str]:
    """Return the column names of a DuckDB table in definition order."""
    rows = connection.execute(f"PRAGMA table_info('{table}')").fetchall()
    # PRAGMA table_info returns (cid, name, type, notnull, dflt_value, pk).
    return [str(row[1]) for row in rows]


def validate_table_schema(
    actual_columns: Iterable[str], schema: TableSchema
) -> SchemaReport:
    """Compare a table's actual columns against its required schema."""
    actual = list(actual_columns)
    actual_set = set(actual)
    required_set = set(schema.required_columns)
    return SchemaReport(
        table=schema.name,
        present=tuple(c for c in schema.required_columns if c in actual_set),
        missing=tuple(c for c in schema.required_columns if c not in actual_set),
        extra=tuple(c for c in actual if c not in required_set),
    )


def validate_connection_schemas(
    connection: Any, schemas: Sequence[TableSchema] = DEFAULT_RAW_SCHEMAS
) -> list[SchemaReport]:
    """Validate every schema against the tables in a DuckDB connection."""
    return [
        validate_table_schema(table_columns(connection, schema.name), schema)
        for schema in schemas
    ]


def assert_no_drift(reports: Iterable[SchemaReport]) -> None:
    """Raise :class:`SchemaDriftError` if any report has missing columns."""
    broken = [report for report in reports if not report.is_valid]
    if broken:
        details = "; ".join(
            f"{report.table} is missing {list(report.missing)}" for report in broken
        )
        raise SchemaDriftError(f"Schema drift detected: {details}")
