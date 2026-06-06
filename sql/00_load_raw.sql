-- Load raw OWID CSV files into DuckDB staging tables.
--
-- DuckDB's CSV reader automatically infers delimiter, header, and types for
-- these files. The raw tables stay close to the source files, but each row
-- carries lightweight ingestion metadata: the source filename and the build
-- timestamp. These columns make it possible to audit where a row came from and
-- when it was loaded.

CREATE OR REPLACE TABLE raw_owid_co2 AS
SELECT
    *,
    '{co2_source}' AS _source_file,
    CAST('{ingested_at}' AS TIMESTAMP) AS _ingested_at
FROM read_csv_auto('{co2_csv}', HEADER = TRUE, SAMPLE_SIZE = -1);

CREATE OR REPLACE TABLE raw_owid_energy AS
SELECT
    *,
    '{energy_source}' AS _source_file,
    CAST('{ingested_at}' AS TIMESTAMP) AS _ingested_at
FROM read_csv_auto('{energy_csv}', HEADER = TRUE, SAMPLE_SIZE = -1);
