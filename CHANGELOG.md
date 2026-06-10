# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project follows
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.0] - 2026-06-10

### Added

- **Uncertainty-aware scoring** (`uncertainty/`): Monte Carlo over weight
  perturbations (Dirichlet samples centred on a profile) producing per-country
  score confidence bands, rank-stability ranges, top-k probability, and an
  uncertain-rank flag. Pure-Python and deterministic given the seed.
- `carbon-duckdb uncertainty` CLI command.
- Notebook `09_uncertainty.ipynb` and `docs/uncertainty.md`.

## [0.6.0] - 2026-06-10

### Added

- **Benchmarking and configurable scoring**: peer-group-relative scoring that
  min-max scales components within a group (EU, OECD, income tiers), versioned
  YAML/JSON scoring profiles (`profiles/`), and a benchmark report with rank,
  percentile, and gaps to the peer median and leader (`benchmark/`).
- `score --group/--profile` options and a `benchmark` CLI command.
- Notebook `08_benchmarking.ipynb` and `docs/benchmarking.md`.

## [0.5.0] - 2026-06-10

### Added

- **Production-style local analytics**: a dbt-duckdb project (`transform/`) that
  rebuilds the marts as tested models; an Evidence.dev BI dashboard
  (`dashboard/`); a scheduled GitHub Actions data-refresh workflow (artifacts);
  and versioned snapshot packaging (`packaging/`, `carbon-duckdb snapshot`).
- A dedicated Dashboard CI workflow, isolated from the Python CI.
- `docs/production.md`.

## [0.4.0] - 2026-06-08

### Added

- **Forecasting and scenarios** (`forecasting/`): OLS trend forecasts with
  approximate prediction intervals, constant-rate scenario comparison tables,
  and policy target-gap analysis.
- `forecast` and `target-gap` CLI commands.
- Notebook `07_forecasting_scenarios.ipynb` and `docs/forecasting.md`.

## [0.3.0] - 2026-06-06

### Added

- **Decomposition and attribution** (`decomposition/`): exact Kaya identity
  decomposition (LMDI, 3- or 4-factor), CO2-per-capita intensity decomposition,
  and electricity-mix / fossil lock-in / industrial-proxy indicators.
- `decompose` CLI command.
- Notebook `06_decomposition_attribution.ipynb` and `docs/decomposition.md`.

## [0.2.0] - 2026-06-06

### Added

- **Data quality and validation** (`quality/`): schema-drift validation,
  missingness reports, country/entity normalization, ISO3 country-group filters,
  row-level ingestion metadata, and reproducible checksum manifests.
- `validate` and `manifest` CLI commands.
- Notebook `05_data_quality.ipynb` and `docs/data_quality.md`.

## [0.1.0] - 2026-05-05

### Added

- Initial local DuckDB transition-analytics lab: synthetic OWID-like data
  generator, OWID downloader, DuckDB builder, SQL staging and country-year mart,
  Parquet exports, transparent transition-risk scoring, and Markdown reports.
- Notebooks `01`-`04` (workflow, score anatomy, exploratory analysis, SQL
  analytics) and a CI workflow running ruff, mypy `--strict`, pytest, and
  headless notebook execution.

[0.7.0]: https://github.com/DiogoRibeiro7/carbon-transition-duckdb-lab/releases/tag/v0.7.0
[0.6.0]: https://github.com/DiogoRibeiro7/carbon-transition-duckdb-lab/compare/v0.6.0...v0.7.0
[0.5.0]: https://github.com/DiogoRibeiro7/carbon-transition-duckdb-lab/compare/v0.5.0...v0.6.0
[0.4.0]: https://github.com/DiogoRibeiro7/carbon-transition-duckdb-lab/compare/v0.4.0...v0.5.0
[0.3.0]: https://github.com/DiogoRibeiro7/carbon-transition-duckdb-lab/compare/v0.3.0...v0.4.0
[0.2.0]: https://github.com/DiogoRibeiro7/carbon-transition-duckdb-lab/compare/v0.2.0...v0.3.0
[0.1.0]: https://github.com/DiogoRibeiro7/carbon-transition-duckdb-lab/releases/tag/v0.1.0
