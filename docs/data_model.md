# Data Model

## Raw layer

### `raw_owid_co2`

Loaded from `owid-co2-data.csv`.

Expected key columns:

- `country`
- `iso_code`
- `year`
- `population`
- `co2`
- `co2_per_capita`

### `raw_owid_energy`

Loaded from `owid-energy-data.csv`.

Expected key columns:

- `country`
- `iso_code`
- `year`
- `primary_energy_consumption`
- `fossil_share_energy`
- `renewables_share_energy`
- `renewables_share_elec`
- `electricity_generation`

## Mart layer

### `mart_country_year_transition`

One row per country and year.

Important fields:

- `country`
- `iso_code`
- `year`
- `population`
- `co2`
- `co2_per_capita`
- `primary_energy_consumption`
- `carbon_intensity`
- `fossil_share_energy`
- `renewables_share_energy`
- `renewables_share_elec`
- `electricity_generation`

### `mart_latest_country_transition`

A convenience table with only the latest available year.
