"""End-to-end DuckDB pipeline orchestration."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from carbon_transition_duckdb.config import ProjectPaths
from carbon_transition_duckdb.database.duckdb_engine import (
    connect,
    execute_sql_file,
    table_to_frame,
)
from carbon_transition_duckdb.quality.country_groups import filter_by_group
from carbon_transition_duckdb.quality.manifest import write_manifest
from carbon_transition_duckdb.quality.schema import (
    assert_no_drift,
    validate_connection_schemas,
)
from carbon_transition_duckdb.risk.scoring import (
    ScoreWeights,
    add_driver_text,
    filter_entities,
    score_transition_risk,
)


@dataclass(frozen=True)
class BuildResult:
    """Result metadata for a DuckDB build run."""

    database: Path
    export_dir: Path
    mart_table: str
    row_count: int
    ingested_at: str
    manifest_path: Path


def _resolve_sql_dir() -> Path:
    """Locate the repository SQL directory for both source and installed runs."""
    sql_dir = Path(__file__).resolve().parents[2] / "sql"
    if not sql_dir.exists():
        # When installed as a package, SQL files may live next to the cwd.
        sql_dir = Path.cwd() / "sql"
    return sql_dir


def build_duckdb_lakehouse(
    paths: ProjectPaths, ingested_at: str | None = None
) -> BuildResult:
    """Build the DuckDB database, analytical mart, and Parquet exports.

    The build also stamps each raw row with ingestion metadata, validates the
    raw schemas against the columns the mart depends on, and writes a checksum
    manifest of the raw inputs.

    Parameters
    ----------
    paths:
        Local raw, database, and export paths.
    ingested_at:
        Optional ingestion timestamp (``YYYY-MM-DD HH:MM:SS``). Defaults to the
        current UTC time; pass an explicit value for reproducible builds.

    Returns
    -------
    BuildResult
        Metadata about the built database.
    """
    paths.ensure()

    if not paths.co2_csv.exists():
        raise FileNotFoundError(f"Missing CO2 CSV file: {paths.co2_csv}")
    if not paths.energy_csv.exists():
        raise FileNotFoundError(f"Missing energy CSV file: {paths.energy_csv}")

    stamp = ingested_at or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    sql_dir = _resolve_sql_dir()

    with connect(paths.database) as connection:
        execute_sql_file(
            connection,
            sql_dir / "00_load_raw.sql",
            {
                "co2_csv": str(paths.co2_csv),
                "energy_csv": str(paths.energy_csv),
                "co2_source": paths.co2_csv.name,
                "energy_source": paths.energy_csv.name,
                "ingested_at": stamp,
            },
        )
        assert_no_drift(validate_connection_schemas(connection))
        execute_sql_file(connection, sql_dir / "01_build_marts.sql")
        execute_sql_file(
            connection,
            sql_dir / "02_export_marts.sql",
            {"export_dir": str(paths.export_dir)},
        )
        row_count = int(
            connection.execute(
                "SELECT COUNT(*) FROM mart_country_year_transition"
            ).fetchone()[0]
        )

    manifest_path = write_manifest(
        [paths.co2_csv, paths.energy_csv],
        paths.database.parent / "data_manifest.json",
    )

    return BuildResult(
        database=paths.database,
        export_dir=paths.export_dir,
        mart_table="mart_country_year_transition",
        row_count=row_count,
        ingested_at=stamp,
        manifest_path=manifest_path,
    )


def load_transition_mart(database: Path) -> pd.DataFrame:
    """Load the country-year transition mart from DuckDB."""
    query = "SELECT * FROM mart_country_year_transition"
    return table_to_frame(database, query)


def compute_transition_scores(
    database: Path,
    exclude_aggregates: bool = True,
    weights: ScoreWeights | None = None,
    group: str | Iterable[str] | None = None,
) -> pd.DataFrame:
    """Compute transition-risk scores from the DuckDB mart.

    Parameters
    ----------
    database:
        Path to the DuckDB database.
    exclude_aggregates:
        Drop aggregate entities (World, Europe, …) before scoring.
    weights:
        Optional scoring weights (e.g. from a profile). Defaults to the balanced
        :class:`ScoreWeights`.
    group:
        Optional peer group (name such as ``"eu"`` / ``"oecd"`` or an iterable of
        ISO3 codes). When given, components are min-max scaled *within* the group
        so scores are relative to comparable economies.
    """
    mart = load_transition_mart(database)
    if exclude_aggregates:
        mart = filter_entities(mart)
    if group is not None:
        mart = filter_by_group(mart, group)
    scores = score_transition_risk(mart, weights=weights)
    return add_driver_text(scores)
