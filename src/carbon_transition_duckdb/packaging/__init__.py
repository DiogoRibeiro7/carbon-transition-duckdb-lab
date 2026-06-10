"""Release packaging utilities (v0.5).

Bundle a built lakehouse -- the DuckDB database, Parquet marts, and the data
manifest -- into a single versioned, shareable snapshot archive.
"""

from __future__ import annotations

from carbon_transition_duckdb.packaging.snapshot import (
    SnapshotResult,
    build_snapshot,
    default_snapshot_path,
)

__all__ = ["SnapshotResult", "build_snapshot", "default_snapshot_path"]
