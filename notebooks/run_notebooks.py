"""Generate quick transition summaries from the country-year mart.

Reads the Parquet mart produced by ``carbon-duckdb build`` (building the
lakehouse on demand if it is missing) and writes a numeric summary, a small
Markdown report, and a per-country record count under ``reports/sample_run/``.

Run from anywhere: ``python notebooks/run_notebooks.py``.
"""

from __future__ import annotations

from pathlib import Path

import duckdb

REPO_ROOT = Path(__file__).resolve().parents[1]
MARTS_DIR = REPO_ROOT / "data" / "processed" / "marts"
MART_PARQUET = MARTS_DIR / "mart_country_year_transition.parquet"
OUT_DIR = REPO_ROOT / "reports" / "sample_run"


def ensure_mart() -> None:
    """Build the lakehouse (with synthetic data) if the Parquet mart is absent."""
    if MART_PARQUET.exists():
        return
    from carbon_transition_duckdb.config import ProjectPaths
    from carbon_transition_duckdb.pipeline import build_duckdb_lakehouse
    from carbon_transition_duckdb.sample_data import generate_synthetic_owid_data

    raw_dir = REPO_ROOT / "data" / "raw"
    if not (raw_dir / "owid-co2-data.csv").exists():
        generate_synthetic_owid_data(raw_dir)
    build_duckdb_lakehouse(
        ProjectPaths(
            raw_dir=raw_dir,
            database=REPO_ROOT / "data" / "processed" / "carbon_transition.duckdb",
            export_dir=MARTS_DIR,
        )
    )


def main() -> None:
    ensure_mart()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Reading", MART_PARQUET)
    df = (
        duckdb.connect()
        .execute(f"SELECT * FROM read_parquet('{MART_PARQUET.as_posix()}')")
        .fetchdf()
    )
    print("Loaded rows:", len(df))

    # Numeric summary
    num_cols = df.select_dtypes(include="number").columns.tolist()
    summary = df[num_cols].describe().transpose()
    summary_path = OUT_DIR / "transition_numeric_summary.csv"
    summary.to_csv(summary_path)
    print("Wrote numeric summary to", summary_path)

    # Markdown report
    report_md = OUT_DIR / "transition_report_from_runner.md"
    with report_md.open("w", encoding="utf8") as f:
        f.write("# Transition numeric summary\n\n")
        f.write(f"Loaded rows: {len(df)}\n\n")
        f.write("Top numeric columns:\n")
        for column in num_cols[:10]:
            f.write(f"- {column}\n")
    print("Wrote markdown report to", report_md)

    # Top countries by records
    country_col = next(
        (c for c in ("country", "Country", "location", "country_name") if c in df.columns),
        None,
    )
    if country_col is not None:
        agg = (
            df.groupby(country_col)
            .size()
            .reset_index(name="records")
            .sort_values("records", ascending=False)
            .head(50)
        )
        top_path = OUT_DIR / "top_countries_by_records.csv"
        agg.to_csv(top_path, index=False)
        print("Wrote top countries CSV to", top_path)
    else:
        print("No country-like column found; skipping top countries aggregation")

    print("Done")


if __name__ == "__main__":
    main()
