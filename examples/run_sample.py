"""Run the full synthetic sample workflow.

This script assumes dependencies are installed and DuckDB is available.
"""

from pathlib import Path

import pandas as pd

from carbon_transition_duckdb.config import ProjectPaths
from carbon_transition_duckdb.pipeline import build_duckdb_lakehouse, compute_transition_scores
from carbon_transition_duckdb.reporting.markdown import write_report
from carbon_transition_duckdb.sample_data import generate_synthetic_owid_data


def main() -> None:
    """Execute the local sample workflow."""
    raw_dir = Path("data/raw")
    database = Path("data/processed/carbon_transition.duckdb")
    export_dir = Path("data/processed/marts")

    generate_synthetic_owid_data(raw_dir, start_year=2010, end_year=2024)
    build_duckdb_lakehouse(ProjectPaths(raw_dir=raw_dir, database=database, export_dir=export_dir))

    scores = compute_transition_scores(database)
    scores_path = Path("reports/sample_run/transition_scores.csv")
    scores_path.parent.mkdir(parents=True, exist_ok=True)
    scores.to_csv(scores_path, index=False)

    write_report(
        pd.read_csv(scores_path),
        output_path=Path("reports/sample_run/transition_report.md"),
        title="Synthetic Carbon Transition Report",
    )


if __name__ == "__main__":
    main()
