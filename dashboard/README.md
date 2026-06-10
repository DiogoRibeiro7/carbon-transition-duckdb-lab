# Carbon Transition Dashboard (Evidence.dev)

A local [Evidence.dev](https://evidence.dev) dashboard over the DuckDB
transition marts built by the Python pipeline (or dbt).

## Prerequisites

- Node.js >= 18
- A built lakehouse. From the repo root:

  ```bash
  poetry run carbon-duckdb sample-data --output-dir data/raw   # or download-owid
  poetry run carbon-duckdb build
  ```

  The dashboard reads `../../../data/processed/carbon_transition.duckdb`
  (configured in `sources/carbon/connection.yaml`).

## Run it

From this `dashboard/` directory:

```bash
npm ci          # reproducible install (uses package-lock.json)
npm run sources # connect to DuckDB and materialise the source queries
npm run dev     # live dev server, or `npm run build` for a static site
```

`npm run build` writes a self-contained static site to `build/`.

## Layout

- `sources/carbon/` — DuckDB connection plus the `transition` and `latest`
  source queries against the marts.
- `pages/index.md` — the dashboard page (KPIs, charts, table).
- `evidence.config.yaml` — theme and the DuckDB datasource plugin.
