# Data Quality & Validation (v0.2)

The `carbon_transition_duckdb.quality` subpackage makes the lab robust against
messy, drifting public data. Every check is transparent and explainable.

## Schema validation

`quality/schema.py` defines the columns each raw table must provide for the
country-year mart to build. The build validates the loaded tables and raises
`SchemaDriftError` if a required column is missing. Extra columns (real OWID
files have hundreds) are reported but never an error.

```python
from carbon_transition_duckdb.quality.schema import validate_connection_schemas
reports = validate_connection_schemas(connection)
```

## Row-level ingestion metadata

`sql/00_load_raw.sql` stamps every raw row with:

- `_source_file` — the originating CSV filename
- `_ingested_at` — the build timestamp (UTC)

The timestamp can be pinned for reproducible builds:

```python
build_duckdb_lakehouse(paths, ingested_at="2025-01-01 00:00:00")
```

## Reproducible manifests

`quality/manifest.py` writes a SHA-256 manifest of the raw inputs to
`data/processed/data_manifest.json` on every build. Re-verifying it detects any
change to the files behind a database.

```bash
poetry run carbon-duckdb manifest --verify
```

## Missingness reports

`quality/missingness.py` quantifies completeness by metric and by country, so a
falling score driven by missing data is never mistaken for a real transition.

```bash
poetry run carbon-duckdb validate --report reports/sample_run/completeness.md
```

## Country normalization

`quality/normalization.py` maps common country aliases ("USA", "Czech Republic")
onto canonical names so cross-source joins and group lookups stay stable.

## Country-group filters

`quality/country_groups.py` defines peer groups by ISO 3166-1 alpha-3 code:

- aggregate-entity removal (World, Europe, income aggregates, …)
- `EU27` (complete) and `OECD` (complete) membership sets
- `INCOME_GROUPS_SAMPLE` — an illustrative World Bank income subset
- `add_group_flags` adds boolean `is_eu` / `is_oecd` columns

See `notebooks/05_data_quality.ipynb` for a runnable tour of all of the above.
