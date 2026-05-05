"""End-to-end DuckDB pipeline orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from carbon_transition_duckdb.config import ProjectPaths
from carbon_transition_duckdb.database.duckdb_engine import connect, execute_sql_file, table_to_frame
from carbon_transition_duckdb.risk.scoring import add_driver_text, filter_entities, score_transition_risk


@dataclass(frozen=True)
class BuildResult:
    """Result metadata for a DuckDB build run."""

    database: Path
    export_dir: Path
    mart_table: str
    row_count: int


def build_duckdb_lakehouse(paths: ProjectPaths) -> BuildResult:
    """Build the DuckDB database, analytical mart, and Parquet exports.

    Parameters
    ----------
    paths:
        Local raw, database, and export paths.

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

    sql_dir = Path(__file__).resolve().parents[2] / "sql"
    if not sql_dir.exists():
        # When installed as a package, SQL files may live next to the project root.
        sql_dir = Path.cwd() / "sql"

    with connect(paths.database) as connection:
        execute_sql_file(
            connection,
            sql_dir / "00_load_raw.sql",
            {
                "co2_csv": str(paths.co2_csv),
                "energy_csv": str(paths.energy_csv),
            },
        )
        execute_sql_file(connection, sql_dir / "01_build_marts.sql")
        execute_sql_file(
            connection,
            sql_dir / "02_export_marts.sql",
            {"export_dir": str(paths.export_dir)},
        )
        row_count = int(connection.execute("SELECT COUNT(*) FROM mart_country_year_transition").fetchone()[0])

    return BuildResult(
        database=paths.database,
        export_dir=paths.export_dir,
        mart_table="mart_country_year_transition",
        row_count=row_count,
    )


def load_transition_mart(database: Path) -> pd.DataFrame:
    """Load the country-year transition mart from DuckDB."""
    query = "SELECT * FROM mart_country_year_transition"
    return table_to_frame(database, query)


def compute_transition_scores(database: Path, exclude_aggregates: bool = True) -> pd.DataFrame:
    """Compute transition-risk scores from the DuckDB mart."""
    mart = load_transition_mart(database)
    if exclude_aggregates:
        mart = filter_entities(mart)
    scores = score_transition_risk(mart)
    return add_driver_text(scores)
