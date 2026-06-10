-- Staging model for the OWID CO2 dataset.
-- Reads the raw CSV directly with DuckDB and selects the typed subset the
-- marts depend on.

with source as (
    select *
    from read_csv_auto('{{ var("raw_dir") }}/owid-co2-data.csv', header = true, sample_size = -1)
)

select
    country,
    iso_code,
    cast(year as integer) as year,
    try_cast(population as double) as population,
    try_cast(co2 as double) as co2,
    try_cast(co2_per_capita as double) as co2_per_capita
from source
where country is not null
  and year is not null
