select
    country,
    iso_code,
    year,
    co2,
    co2_per_capita,
    carbon_intensity,
    fossil_share_energy,
    renewables_share_elec
from mart_latest_country_transition
order by co2 desc
