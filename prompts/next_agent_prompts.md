# Prompts for Coding Agents

## Add dbt-duckdb support

Implement a `dbt/` project using `dbt-duckdb`. Move the SQL transformation
logic from `sql/` into dbt models with tests for not-null keys and accepted
ranges.

## Add data quality checks

Create a `quality/` module that checks missingness, country-year coverage,
column drift, duplicate keys, impossible values, and abrupt source changes.

## Add Kaya identity decomposition

Implement a decomposition notebook using population, GDP, energy intensity,
and carbon intensity when the required columns are available.

## Add scenario gap analysis

Create a module that compares observed emissions trajectories with simple
target pathways, including linear, exponential, and user-defined scenarios.

## Add country group support

Add static country-group mapping files and CLI filters for EU, OECD, G20,
income groups, and custom user-defined country sets.
