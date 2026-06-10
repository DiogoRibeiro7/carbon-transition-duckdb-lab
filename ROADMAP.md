# Roadmap

## v0.1 — Local DuckDB transition analytics

- [x] Synthetic OWID-like data generator
- [x] OWID downloader
- [x] DuckDB database builder
- [x] SQL staging layer
- [x] Country-year transition mart
- [x] Parquet mart export
- [x] Transparent transition-risk scoring
- [x] Markdown report generation
- [x] Notebook workflow
- [x] Tests for pure transformation logic

## v0.2 — Data quality and validation

- [x] Add schema validation for OWID column drift
- [x] Add missingness reports by country and metric
- [x] Add country/entity normalization
- [x] Add country group filters: World, EU, OECD, income groups
- [x] Add row-level ingestion metadata
- [x] Add reproducible data manifests with checksums

## v0.3 — Decomposition and attribution

- [x] Kaya identity decomposition
- [x] Emissions intensity decomposition
- [x] Electricity mix transition indicators
- [x] Fossil lock-in indicators
- [x] Industrial emissions proxy indicators

## v0.4 — Forecasting and scenarios

- [x] Baseline trend forecasts
- [x] Uncertainty intervals
- [x] Scenario comparison tables
- [x] Policy target gap analysis

## v0.5 — Production-style local analytics

- [x] dbt-duckdb integration
- [x] Evidence.dev or Quarto dashboard
- [x] Scheduled GitHub Actions data refresh
- [x] Release packaged DuckDB snapshots
