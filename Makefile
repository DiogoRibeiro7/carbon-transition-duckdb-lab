.PHONY: install test lint format notebooks sample build score report

install:
	poetry install --with dev

test:
	poetry run pytest

lint:
	poetry run ruff check .
	poetry run mypy src

notebooks:
	poetry run pytest --nbmake notebooks

format:
	poetry run ruff format .
	poetry run ruff check . --fix

sample:
	poetry run carbon-duckdb sample-data --output-dir data/raw --start-year 2010 --end-year 2024

build:
	poetry run carbon-duckdb build --raw-dir data/raw --database data/processed/carbon_transition.duckdb --export-dir data/processed/marts

score:
	poetry run carbon-duckdb score --database data/processed/carbon_transition.duckdb --output reports/sample_run/transition_scores.csv

report:
	poetry run carbon-duckdb report --scores reports/sample_run/transition_scores.csv --output reports/sample_run/transition_report.md
