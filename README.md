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
├── AGENTS.md
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
│   ├── reporting/
│   ├── visualization/
│   ├── sample_data.py
│   ├── pipeline.py
│   └── cli.py
├── notebooks/
│   └── 01_duckdb_transition_workflow.ipynb
├── tests/
├── reports/
└── prompts/
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
