select
    country,
    iso_code,
    year,
    co2,
    co2_per_capita,
    primary_energy_consumption,
    carbon_intensity,
    fossil_share_energy,
    renewables_share_energy,
    renewables_share_elec
from mart_country_year_transition
order by country, year
