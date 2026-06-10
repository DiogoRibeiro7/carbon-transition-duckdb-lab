# Production-Style Local Analytics (v0.5)

v0.5 wraps the lab in production-style tooling: an analytics-engineering layer,
a BI dashboard, scheduled refresh, and shareable snapshots.

## dbt-duckdb

The `transform/` directory is a [dbt](https://docs.getdbt.com) project that
rebuilds the same marts as the Python pipeline, so the SQL is testable and
documented as analytics-engineering models.

```bash
poetry run carbon-duckdb sample-data --output-dir data/raw
poetry run dbt build --project-dir transform --profiles-dir transform
```

- `models/staging/` — typed views over the raw OWID CSVs (read with DuckDB).
- `models/marts/` — `mart_country_year_transition` and `mart_latest_country_transition`.
- `_staging.yml` / `_marts.yml` — `not_null` tests on the key columns.

Paths are resolved relative to the repo root (`vars.raw_dir`, the DuckDB
`path`), so always invoke dbt from the repo root.

## Evidence.dev dashboard

The `dashboard/` directory is an [Evidence](https://evidence.dev) project that
reads the DuckDB marts and renders a static BI site.

```bash
poetry run carbon-duckdb build            # build the lakehouse first
cd dashboard && npm ci && npm run sources && npm run dev
```

`npm run build` writes a self-contained static site to `dashboard/build/`. See
`dashboard/README.md` for details. The Evidence build runs in its own CI
workflow (`.github/workflows/dashboard.yml`) so it never gates the Python CI.

## Scheduled data refresh

`.github/workflows/data-refresh.yml` runs weekly (and on manual dispatch). It
downloads the live OWID data, rebuilds, validates, scores, packages a snapshot,
and uploads the snapshot + reports as workflow **artifacts**. Nothing is
committed back or published as a release.

## Release snapshots

Package a built lakehouse into a single versioned archive:

```bash
poetry run carbon-duckdb snapshot
# -> dist/carbon_transition_snapshot_v0.5.0.zip
```

The archive bundles the DuckDB database, the Parquet marts, and the data
manifest, with a `SNAPSHOT_VERSION` marker. It is reproducible from the same
inputs and convenient to attach to a release or share for offline analysis.
