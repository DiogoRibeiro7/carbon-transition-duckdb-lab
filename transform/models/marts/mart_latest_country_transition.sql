-- Latest available year of the country-year transition mart.

select *
from {{ ref('mart_country_year_transition') }}
where year = (select max(year) from {{ ref('mart_country_year_transition') }})
