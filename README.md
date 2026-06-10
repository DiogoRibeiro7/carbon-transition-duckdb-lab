# Carbon Transition DuckDB Lab

A local analytical lakehouse for climate and energy-transition analysis.

The project downloads public climate and energy datasets, stores the raw files locally,
builds a DuckDB database, materializes Parquet marts, and runs transparent country-year
transition-risk scoring notebooks.

The goal is not to produce a single "truth" about climate performance. The goal is to
make the assumptions visible: emissions, emissions intensity, fossil share, renewable
share, recent trends, and data completeness.

## Why DuckDB?

DuckDB is used as the embedded analytical engine. The repository stores data locally
and executes SQL directly over CSV and Parquet files. This makes it practical for a
single-machine data science workflow without running a database server.

## Data sources

The production workflow is prepared for:

- Our World in Data CO2 and Greenhouse Gas Emissions dataset
- Our World in Data Energy dataset

The repository also includes a synthetic OWID-like data generator so the full workflow
can be tested without downloading the real files.

## What v0.1 does

```text
OWID CSV downloads / synthetic data
        ↓
local raw storage
        ↓
DuckDB database
        ↓
SQL staging tables
        ↓
country-year analytical mart
        ↓
Parquet exports
        ↓
transition risk scores
        ↓
Markdown report + notebook
```

## Repository layout

```text
carbon-transition-duckdb-lab/
├── README.md
├── ROADMAP.md
├── CITATION.cff
├── pyproject.toml
├── Makefile
├── setup.sh
├── sql/
│   ├── 00_load_raw.sql
│   ├── 01_build_marts.sql
│   └── 02_export_marts.sql
├── src/carbon_transition_duckdb/
│   ├── ingestion/
│   ├── database/
│   ├── risk/
│   ├── quality/
│   ├── decomposition/
│   ├── forecasting/
│   ├── packaging/
│   ├── reporting/
│   ├── visualization/
│   ├── sample_data.py
│   ├── pipeline.py
│   └── cli.py
├── transform/            # dbt-duckdb project (staging + marts)
├── dashboard/            # Evidence.dev BI dashboard
├── notebooks/
│   ├── 01_duckdb_transition_workflow.ipynb
│   ├── 02_score_anatomy_and_sensitivity.ipynb
│   ├── 03_exploratory_analysis.ipynb
│   ├── 04_duckdb_sql_analytics.ipynb
│   ├── 05_data_quality.ipynb
│   ├── 06_decomposition_attribution.ipynb
│   └── 07_forecasting_scenarios.ipynb
├── tests/
└── reports/
```

## Install

```bash
poetry install --with dev
```

## Run with synthetic data

Generate local sample data:

```bash
poetry run carbon-duckdb sample-data \
  --output-dir data/raw \
  --start-year 2010 \
  --end-year 2024
```

Build the DuckDB database and marts:

```bash
poetry run carbon-duckdb build \
  --raw-dir data/raw \
  --database data/processed/carbon_transition.duckdb \
  --export-dir data/processed/marts
```

Score transition risk:

```bash
poetry run carbon-duckdb score \
  --database data/processed/carbon_transition.duckdb \
  --output reports/sample_run/transition_scores.csv
```

Generate a report:

```bash
poetry run carbon-duckdb report \
  --scores reports/sample_run/transition_scores.csv \
  --output reports/sample_run/transition_report.md \
  --title "Sample Carbon Transition Report"
```

## Download real OWID data

```bash
poetry run carbon-duckdb download-owid --output-dir data/raw
```

Then run the same `build`, `score`, and `report` commands.

## Data quality (v0.2)

The `build` step now stamps raw rows with ingestion metadata, validates the raw
schemas against the columns the mart needs, and writes a checksum manifest.
Two commands expose the data-quality layer directly:

```bash
# Validate raw schemas + report completeness (writes an optional Markdown report)
poetry run carbon-duckdb validate \
  --database data/processed/carbon_transition.duckdb \
  --report reports/sample_run/completeness.md

# Verify the raw files still match the recorded manifest
poetry run carbon-duckdb manifest --verify
```

See [docs/data_quality.md](docs/data_quality.md) for the full toolkit
(schema validation, missingness, normalization, country groups, manifests).

## Decomposition & attribution (v0.3)

Explain *why* emissions changed with an exact Kaya identity (LMDI) decomposition,
a CO2-per-capita decomposition, and transition indicators:

```bash
# Kaya decomposition of CO2 change (population / energy / carbon intensity)
poetry run carbon-duckdb decompose --method kaya

# CO2-per-capita decomposition over a custom window
poetry run carbon-duckdb decompose --method intensity --start-year 2015 --end-year 2024

# Electricity-mix, fossil lock-in and industrial-proxy indicators
poetry run carbon-duckdb decompose --method indicators --output reports/sample_run/indicators.csv
```

See [docs/decomposition.md](docs/decomposition.md) for the method details.

## Forecasting & scenarios (v0.4)

Transparent baseline projections that assume the recent trend continues:

```bash
# OLS trend forecast with ~95% prediction intervals
poetry run carbon-duckdb forecast --metric co2 --horizon 6

# Gap to a 30%-by-2030 reduction target (vs. a 2010 base year)
poetry run carbon-duckdb target-gap --metric co2 --base-year 2010 --target-year 2030 --reduction 0.30
```

Scenario comparison tables and the full method (intervals, CAGR scenarios,
target gaps) are documented in [docs/forecasting.md](docs/forecasting.md).

## Production-style local analytics (v0.5)

- **dbt-duckdb** (`transform/`) rebuilds the marts as tested dbt models:

  ```bash
  poetry run carbon-duckdb sample-data --output-dir data/raw
  poetry run dbt build --project-dir transform --profiles-dir transform
  ```

- **Evidence.dev dashboard** (`dashboard/`) renders the marts as a BI site:

  ```bash
  poetry run carbon-duckdb build
  cd dashboard && npm ci && npm run sources && npm run dev
  ```

- **Release snapshot** bundles the database, marts, and manifest into a zip:

  ```bash
  poetry run carbon-duckdb snapshot   # -> dist/carbon_transition_snapshot_v0.5.0.zip
  ```

- **Scheduled refresh** (`.github/workflows/data-refresh.yml`) downloads live
  OWID data weekly and uploads a fresh snapshot + reports as artifacts.

Full details in [docs/production.md](docs/production.md).

## Main metrics

The first version computes a transparent score from:

- recent CO2 emissions trend
- CO2 per capita
- carbon intensity of energy
- fossil-fuel share of primary energy
- renewable electricity share
- data completeness

The score is not a moral ranking. It is an exploratory signal to identify countries
or regions that deserve deeper investigation.

## Example analytical SQL

```sql
SELECT
    country,
    year,
    co2,
    co2_per_capita,
    fossil_share_energy,
    renewables_share_elec,
    transition_risk_score
FROM mart_transition_scores
WHERE year = (SELECT MAX(year) FROM mart_transition_scores)
ORDER BY transition_risk_score DESC
LIMIT 20;
```

## Notebooks

The `notebooks/` directory contains a runnable, output-embedded tour of the lab.
Each notebook resolves the repository root automatically and builds the DuckDB
lakehouse on demand, so they can be run in any order.

| Notebook | What it covers |
| --- | --- |
| `01_duckdb_transition_workflow.ipynb` | End-to-end workflow: generate data → build DuckDB → inspect with SQL → score → visualize → report. |
| `02_score_anatomy_and_sensitivity.ipynb` | Decomposes the score into weighted components and tests how robust the ranking is to different weight choices. |
| `03_exploratory_analysis.ipynb` | Exploratory analysis of the country-year panel: trends, distributions, correlations, and energy-mix trajectories. |
| `04_duckdb_sql_analytics.ipynb` | Pure-SQL analytics over the Parquet marts: window functions, CAGR, per-year rankings, and custom mart exports. |
| `05_data_quality.ipynb` | Data-quality toolkit (v0.2): schema-drift validation, ingestion metadata, checksum manifests, missingness reports, country normalization, and group filters. |
| `06_decomposition_attribution.ipynb` | Decomposition & attribution (v0.3): Kaya identity (LMDI), emissions-intensity decomposition, and fossil lock-in / electricity-mix indicators. |
| `07_forecasting_scenarios.ipynb` | Forecasting & scenarios (v0.4): OLS trend forecasts with prediction intervals, constant-rate scenario comparison, and policy target-gap analysis. |

Run them from the project environment, for example:

```bash
poetry run jupyter lab notebooks/
```

To re-execute a notebook headlessly and embed fresh outputs:

```bash
poetry run jupyter nbconvert --to notebook --execute --inplace \
  notebooks/01_duckdb_transition_workflow.ipynb
```

## Responsible use

This project should not be used to make simplistic claims about national performance.
Energy systems are constrained by geography, income, industrial structure, trade,
historical emissions, infrastructure, and data quality. The score is a transparent
screening tool, not a final judgement.

## Create the GitHub repo

```bash
gh repo create carbon-transition-duckdb-lab \
  --public \
  --source=. \
  --remote=origin \
  --push \
  --description "Local DuckDB lakehouse for climate and energy-transition analytics"
```

Add topics:

```bash
gh repo edit DiogoRibeiro7/carbon-transition-duckdb-lab \
  --add-topic duckdb \
  --add-topic climate-risk \
  --add-topic energy-transition \
  --add-topic data-engineering \
  --add-topic parquet \
  --add-topic analytics-engineering
```
