"""DuckDB connection and SQL execution utilities."""

from __future__ import annotations

from pathlib import Path


def _import_duckdb():
    """Import DuckDB with a clear error if the dependency is missing."""
    try:
        import duckdb  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "DuckDB is required for this command. Install dependencies with "
            "`poetry install --with dev` or `pip install duckdb`."
        ) from exc
    return duckdb


def connect(database: Path):
    """Open or create a local DuckDB database."""
    duckdb = _import_duckdb()
    database.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(database))


def execute_sql_file(connection, sql_path: Path, parameters: dict[str, str] | None = None) -> None:
    """Execute a SQL file against a DuckDB connection.

    Parameters are replaced using simple `{name}` placeholders. This is intended
    only for trusted repository SQL files and internal path substitution.
    """
    sql = sql_path.read_text(encoding="utf-8")
    for key, value in (parameters or {}).items():
        sql = sql.replace("{" + key + "}", value.replace("'", "''"))
    connection.execute(sql)


def table_to_frame(database: Path, query: str):
    """Run a query against a database and return a pandas DataFrame."""
    with connect(database) as connection:
        return connection.execute(query).fetchdf()
