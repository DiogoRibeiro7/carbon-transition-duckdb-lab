-- Staging model for the OWID energy dataset.

with source as (
    select *
    from read_csv_auto('{{ var("raw_dir") }}/owid-energy-data.csv', header = true, sample_size = -1)
)

select
    country,
    cast(year as integer) as year,
    try_cast(primary_energy_consumption as double) as primary_energy_consumption,
    try_cast(fossil_share_energy as double) as fossil_share_energy,
    try_cast(renewables_share_energy as double) as renewables_share_energy,
    try_cast(renewables_share_elec as double) as renewables_share_elec,
    try_cast(electricity_generation as double) as electricity_generation
from source
where country is not null
  and year is not null
