-- Build analytical country-year mart.
--
-- The mart keeps the columns needed for transparent transition-risk scoring.
-- Where a metric is missing or undefined, the value remains NULL. The Python
-- scoring layer handles missingness explicitly.

CREATE OR REPLACE TABLE mart_country_year_transition AS
SELECT
    co2.country,
    co2.iso_code,
    CAST(co2.year AS INTEGER) AS year,
    TRY_CAST(co2.population AS DOUBLE) AS population,
    TRY_CAST(co2.co2 AS DOUBLE) AS co2,
    TRY_CAST(co2.co2_per_capita AS DOUBLE) AS co2_per_capita,
    TRY_CAST(energy.primary_energy_consumption AS DOUBLE) AS primary_energy_consumption,
    CASE
        WHEN TRY_CAST(energy.primary_energy_consumption AS DOUBLE) > 0
        THEN TRY_CAST(co2.co2 AS DOUBLE) / TRY_CAST(energy.primary_energy_consumption AS DOUBLE)
        ELSE NULL
    END AS carbon_intensity,
    TRY_CAST(energy.fossil_share_energy AS DOUBLE) AS fossil_share_energy,
    TRY_CAST(energy.renewables_share_energy AS DOUBLE) AS renewables_share_energy,
    TRY_CAST(energy.renewables_share_elec AS DOUBLE) AS renewables_share_elec,
    TRY_CAST(energy.electricity_generation AS DOUBLE) AS electricity_generation
FROM raw_owid_co2 AS co2
LEFT JOIN raw_owid_energy AS energy
    ON co2.country = energy.country
   AND CAST(co2.year AS INTEGER) = CAST(energy.year AS INTEGER)
WHERE co2.country IS NOT NULL
  AND co2.year IS NOT NULL;

CREATE OR REPLACE TABLE mart_latest_country_transition AS
SELECT *
FROM mart_country_year_transition
WHERE year = (SELECT MAX(year) FROM mart_country_year_transition);
