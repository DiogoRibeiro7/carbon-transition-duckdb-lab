-- Load raw OWID CSV files into DuckDB staging tables.
--
-- DuckDB's CSV reader automatically infers delimiter, header, and types for
-- these files. The raw tables are intentionally close to the source files.

CREATE OR REPLACE TABLE raw_owid_co2 AS
SELECT *
FROM read_csv_auto('{co2_csv}', HEADER = TRUE, SAMPLE_SIZE = -1);

CREATE OR REPLACE TABLE raw_owid_energy AS
SELECT *
FROM read_csv_auto('{energy_csv}', HEADER = TRUE, SAMPLE_SIZE = -1);
