-- Export analytical marts to local Parquet files.

COPY mart_country_year_transition
TO '{export_dir}/mart_country_year_transition.parquet'
(FORMAT PARQUET);

COPY mart_latest_country_transition
TO '{export_dir}/mart_latest_country_transition.parquet'
(FORMAT PARQUET);
