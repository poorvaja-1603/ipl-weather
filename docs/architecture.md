# Architecture and System Design

## 1. Overview
The pipeline ingests IPL match and ball-by-ball deliveries data alongside historical hourly weather data, stores and models it in Snowflake using dbt, orchestrates the entire flow via Apache Airflow, and exposes an interactive conversational BI application powered by Gemini and Streamlit.

## 2. End-to-End Data Flow

```
IPL matches.csv + deliveries.csv (HTTPS)           Open-Meteo Archive API (REST)
              |                                                   |
       Airbyte File source                         Airbyte custom source (Connector Builder)
              |                                                   |
              +---------------------> Airbyte -------------------+
                                         |
                               Snowflake  IPL_DB.RAW
                                         |
                                   dbt (STAGING)
                         seeds: venue_map, team_map
                         stg_matches, stg_deliveries, stg_weather_hourly
                                         |
                              dbt intermediate (views)
                      int_innings_totals, int_match_weather
                                         |
                                  dbt (MARTS)
        dim_team, dim_venue, fct_match, fct_innings, mart_* tables
                                         |
                       Streamlit + Gemini (read-only BI_ROLE)
                                         ^
          Airflow DAG orchestrates every step above end to end
```

## 3. Airflow Orchestration DAG
```
check_sources >> [sync_ipl_csv, sync_weather] >> validate_raw
>> dbt_deps >> dbt_seed >> dbt_run >> dbt_test >> refresh_bi_context >> notify_success
```

## 4. Security and Access Control
- Least privilege model enforced in Snowflake:
  - `AIRBYTE_ROLE`: read/write on `IPL_DB.RAW`.
  - `TRANSFORM_ROLE`: read on `RAW`, full schema ownership on `STAGING` and `MARTS`.
  - `BI_ROLE`: read-only SELECT permissions strictly on `IPL_DB.MARTS`.
- SQL Guard validates incoming LLM queries with `sqlglot`:
  - Disallows mutations (DDL/DML).
  - Enforces single statement `SELECT`.
  - Blocks access to non-MARTS tables.
  - Automatically appends safety `LIMIT 200`.
