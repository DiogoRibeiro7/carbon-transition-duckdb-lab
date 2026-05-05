# Agent Instructions

This repository is a local analytical lakehouse built around DuckDB.

## Development principles

1. Keep the workflow local-first.
2. Prefer SQL for analytical transformations.
3. Keep Python for orchestration, scoring, validation, and reporting.
4. Do not introduce a database server.
5. Keep risk scores transparent and explainable.
6. Avoid causal claims about climate policy effectiveness.
7. Add tests for all non-trivial transformation logic.
8. Keep notebooks reproducible and light.

## Coding style

- Use type hints.
- Use dataclasses for configuration objects.
- Add docstrings to public functions.
- Validate path inputs.
- Raise clear exceptions.
- Keep CLI commands composable.

## Data handling

Raw data should go into `data/raw/`.
DuckDB databases should go into `data/processed/`.
Exported marts should go into `data/processed/marts/`.
Reports should go into `reports/`.

Do not commit large real datasets.
Commit only small synthetic examples when needed.
