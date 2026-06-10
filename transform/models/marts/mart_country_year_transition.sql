-- Country-year analytical mart (dbt build of sql/01_build_marts.sql).
-- Mirrors the Python pipeline's mart so dbt and the embedded SQL stay in lockstep.

with co2 as (
    select * from {{ ref('stg_owid_co2') }}
),

energy as (
    select * from {{ ref('stg_owid_energy') }}
)

select
    co2.country,
    co2.iso_code,
    co2.year,
    co2.population,
    co2.co2,
    co2.co2_per_capita,
    energy.primary_energy_consumption,
    case
        when energy.primary_energy_consumption > 0
        then co2.co2 / energy.primary_energy_consumption
        else null
    end as carbon_intensity,
    energy.fossil_share_energy,
    energy.renewables_share_energy,
    energy.renewables_share_elec,
    energy.electricity_generation
from co2
left join energy
    on co2.country = energy.country
   and co2.year = energy.year
