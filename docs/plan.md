# IPL + Weather Impact: End-to-End Data Pipeline (DE Microproject)

Team of 2 (Member A, Member B). Demo and submission: 16 and 17 Nov 2026 in lab sessions. Today is 13 Nov 2026, so the build window is about 3 days. Scope is deliberately tight.

---

## 0. Instructions for the coding agent (read first)

1. Read this whole file before doing anything.
2. Work phase by phase (Section 13). At the end of each phase, give a short summary of what exists and what was verified, then stop and wait for approval. Do not ask for approval on trivial choices.
3. The user will say which member they are acting as ("acting as A" or "acting as B"). Only touch that member's folders (Section 4) unless told otherwise. Shared files (README, docker-compose, .env.example) need a note in the summary when changed.
4. Code style:
   - Clean, simple, explainable by second-year students. No clever one-liners.
   - No unnecessary comments, no decorative docstrings. Only comment where logic is non-obvious.
   - No em dashes or en dashes in any text, comments, docs or UI strings. Use hyphens or commas.
   - Small functions, clear names, type hints where cheap.
5. Never hardcode secrets. Everything comes from `.env` (see `.env.example`). `.env` is gitignored.
6. Provider versions, connector UIs and auth methods change often (Airbyte API auth, Airflow 2 vs 3, Snowflake MFA rules, Gemini model names). Check current official docs before writing config. If a step in this plan does not work as written, propose the smallest fix and tell the user. Do not silently swap technologies.
7. Inspect the real CSV headers before writing any staging model. Column names in this plan are typical, not guaranteed.
8. Do not add Spark, Kafka, Kubernetes, Terraform or any extra tooling. The stack is fixed (Section 2).
9. Every phase must end with a runnable, verifiable state (commands in Section 12).

---

## 1. Project summary

**Title:** Does the weather decide the chase? IPL match analytics with a conversational BI layer.

**Idea:** Join IPL ball-by-ball and match data with hourly historical weather (temperature, humidity, dew point, rain, wind) at each venue. Answer questions like "Which venue has the best chase win rate when humidity is above 70%?" through a natural language chat interface.

**Why it fits the rubric:** batch ingestion with Airbyte from two different source types (CSV files and a REST API), Airflow DAG orchestration, dbt staging and marts with tests and docs, a cloud warehouse, and a conversational BI interface that converts questions to SQL.

**Report template mapping:** Section 15.

---

## 2. Final decisions (do not revisit)

| Layer          | Choice                                              | Notes                                            |
| -------------- | --------------------------------------------------- | ------------------------------------------------ |
| Orchestration  | Apache Airflow in Docker (LocalExecutor + Postgres) | Custom image includes dbt                        |
| Ingestion      | Airbyte (local via `abctl`)                         | Two connections: CSV and weather                 |
| Warehouse      | Snowflake (free trial, XSMALL, auto-suspend 60s)    | BigQuery is a possible swap, see Section 16      |
| Transformation | dbt Core with `dbt-snowflake`                       | Seeds, staging, intermediate, marts, tests, docs |
| BI interface   | Streamlit + Gemini text-to-SQL                      | Read-only role, SQL guard, charts                |
| Language       | Python 3.11+                                        |                                                  |
| VCS            | One GitHub repo, branches per member                |                                                  |

Assume Docker Desktop is available. On Windows, use WSL2.

---

## 3. Architecture and data flow

```
IPL matches.csv + deliveries.csv (HTTPS raw files)       Open-Meteo Archive API (REST)
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

Airflow DAG `ipl_weather_pipeline`:

```
check_sources >> [sync_ipl_csv, sync_weather] >> validate_raw
>> dbt_deps >> dbt_seed >> dbt_run >> dbt_test >> refresh_bi_context >> notify_success
```

---

## 4. Team split (equal load) and folder ownership

### Member A: Platform, Ingestion, Orchestration

| #   | Task                                                                                                          | Output                                      |
| --- | ------------------------------------------------------------------------------------------------------------- | ------------------------------------------- |
| A1  | Repo setup, `.env.example`, `.gitignore`, README skeleton                                                     | Repo                                        |
| A2  | Snowflake account, roles, schemas (Section 7)                                                                 | `infra/snowflake_setup.sql`                 |
| A3  | Airflow in Docker with custom image (dbt, Airbyte, Snowflake providers)                                       | `docker-compose.yml`, `Dockerfile`          |
| A4  | Airbyte via `abctl`, CSV source and destination, connection `ipl_csv_to_snowflake`                            | `airbyte/` notes                            |
| A5  | Venue and team seeds from the real data, with verified coordinates                                            | `seeds/venue_map.csv`, `seeds/team_map.csv` |
| A6  | Weather partitions script and Airbyte Connector Builder source, connection `weather_to_snowflake`             | `scripts/`, `airbyte/weather_source.yaml`   |
| A7  | dbt staging layer: `stg_matches`, `stg_deliveries`, `stg_weather_hourly` + source definitions + staging tests | `dbt/ipl_dbt/models/staging/`               |
| A8  | Airflow DAG with retries, sensors, failure callback, dbt tasks                                                | `airflow/dags/ipl_pipeline_dag.py`          |
| A9  | Raw validation checks (row counts, null keys) task                                                            | inside DAG                                  |
| A10 | Report: cover, abstract, sections 1, 2, 3.Ingestion, 3.Orchestration                                          | `docs/report/`                              |

### Member B: Modeling, Marts, Conversational BI

| #   | Task                                                                                  | Output                       |
| --- | ------------------------------------------------------------------------------------- | ---------------------------- |
| B1  | dbt project init, `profiles.yml` via env vars, `packages.yml`, schema macro           | `dbt/ipl_dbt/`               |
| B2  | Intermediate models: `int_innings_totals`, `int_match_weather`                        | `models/intermediate/`       |
| B3  | Dimensions and facts: `dim_team`, `dim_venue`, `fct_match`, `fct_innings`             | `models/marts/`              |
| B4  | Analytical marts (Section 10.4)                                                       | `models/marts/`              |
| B5  | dbt tests, descriptions on every mart column, docs generation, source freshness       | `schema.yml`, `target/` docs |
| B6  | BI context builder from dbt `manifest.json` and `catalog.json`                        | `bi/schema_context.py`       |
| B7  | Streamlit app: chat, text-to-SQL with Gemini, SQL guard, retry, table, chart, summary | `bi/`                        |
| B8  | Evaluation set of 15 questions with gold SQL and an eval runner                       | `bi/eval/`                   |
| B9  | Report: sections 3.Transformation, 3.Warehouse and BI, 4, 5, screenshots              | `docs/report/`               |
| B10 | Demo dataset sanity checks (known facts verified against marts)                       | notes in `docs/`             |

### Shared

- Integration on Day 3, full DAG run, demo rehearsal (twice), backup demo video.
- Cross-walkthrough: each member explains the other's half to the other for 30 minutes on Day 3. Viva questions will hit both halves.

### Folder ownership (avoid merge conflicts)

| Path                                                                                                        | Owner          |
| ----------------------------------------------------------------------------------------------------------- | -------------- |
| `infra/`, `airbyte/`, `airflow/`, `scripts/`, `docker-compose.yml`, `Dockerfile`                            | A              |
| `dbt/ipl_dbt/seeds/`, `dbt/ipl_dbt/models/staging/`                                                         | A              |
| `dbt/ipl_dbt/dbt_project.yml`, `packages.yml`, `macros/`, `models/intermediate/`, `models/marts/`, `tests/` | B              |
| `bi/`                                                                                                       | B              |
| `docs/report/` sections                                                                                     | per Section 15 |

### Interface contract (so both can work in parallel from hour 2)

A must deliver these Snowflake objects first, even if loaded manually from the CSVs through the Snowflake UI, so B is unblocked:

- `IPL_DB.RAW.IPL_MATCHES` (one row per match)
- `IPL_DB.RAW.IPL_DELIVERIES` (one row per ball)
- `IPL_DB.RAW.WEATHER_HOURLY` (one row per venue-date-range partition, with hourly arrays, see Section 8.3)

A must deliver these staging models with this exact shape:

- `stg_matches`: `match_id`, `season_year`, `match_date`, `venue_id`, `team1_id`, `team2_id`, `toss_winner_id`, `toss_decision`, `winner_id`, `result_type`, `result_margin`, `player_of_match`, `dl_applied`, `is_super_over`
- `stg_deliveries`: `match_id`, `innings_no`, `over_no`, `ball_no`, `batting_team_id`, `bowling_team_id`, `batter`, `bowler`, `batter_runs`, `extra_runs`, `total_runs`, `is_wicket`, `dismissal_kind`
- `stg_weather_hourly`: `venue_id`, `observed_at` (local time), `temperature_c`, `humidity_pct`, `dew_point_c`, `precipitation_mm`, `wind_kmh`

B builds everything downstream of those three.

---

## 5. Repo structure

```
ipl-pipeline/
  README.md
  plan.md
  .env.example
  .gitignore
  Dockerfile
  docker-compose.yml
  requirements.txt
  infra/
    snowflake_setup.sql
  airbyte/
    README.md
    weather_source.yaml
    weather_partitions.json
  airflow/
    dags/
      ipl_pipeline_dag.py
  scripts/
    build_venue_list.py
    build_weather_partitions.py
  dbt/
    ipl_dbt/
      dbt_project.yml
      packages.yml
      profiles.yml
      macros/
        generate_schema_name.sql
      seeds/
        venue_map.csv
        team_map.csv
      models/
        staging/
          _sources.yml
          _staging.yml
          stg_matches.sql
          stg_deliveries.sql
          stg_weather_hourly.sql
        intermediate/
          int_innings_totals.sql
          int_match_weather.sql
        marts/
          _marts.yml
          dim_team.sql
          dim_venue.sql
          fct_match.sql
          fct_innings.sql
          mart_venue_stats.sql
          mart_weather_impact.sql
          mart_team_season.sql
          mart_batter_season.sql
          mart_bowler_season.sql
          mart_batter_weather.sql
      tests/
        assert_innings_total_matches_deliveries.sql
  bi/
    app.py
    config.py
    db.py
    llm.py
    sql_guard.py
    charts.py
    schema_context.py
    context/
      schema_context.md
    eval/
      questions.yaml
      run_eval.py
  docs/
    architecture.md
    report/
```

---

## 6. Environment and secrets

`.env.example` must contain:

```
SNOWFLAKE_ACCOUNT=
SNOWFLAKE_WAREHOUSE=IPL_WH
SNOWFLAKE_DATABASE=IPL_DB

SNOWFLAKE_DBT_USER=
SNOWFLAKE_DBT_PASSWORD=
SNOWFLAKE_DBT_ROLE=TRANSFORM_ROLE

SNOWFLAKE_BI_USER=
SNOWFLAKE_BI_PASSWORD=
SNOWFLAKE_BI_ROLE=BI_ROLE

AIRBYTE_API_URL=http://host.docker.internal:8000
AIRBYTE_CLIENT_ID=
AIRBYTE_CLIENT_SECRET=
AIRBYTE_CSV_CONNECTION_ID=
AIRBYTE_WEATHER_CONNECTION_ID=

IPL_MATCHES_URL=
IPL_DELIVERIES_URL=

GEMINI_API_KEY=
GEMINI_MODEL=
```

Notes:

- If Snowflake blocks password login for service users because of MFA policy, use key-pair authentication for `AIRBYTE_USER` and `DBT_USER`, and document it in the README.
- `GEMINI_MODEL`: use a currently available Flash-class model from the official docs.
- The CSVs are hosted in a public GitHub repo (raw URLs) so Airbyte's File source can read them over HTTPS. Stretch option: S3 bucket and the Airbyte S3 source.

---

## 7. Snowflake setup (A2)

Create `infra/snowflake_setup.sql` with the following (replace passwords, do not commit real ones):

```sql
USE ROLE ACCOUNTADMIN;

CREATE WAREHOUSE IF NOT EXISTS IPL_WH
  WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE;

CREATE DATABASE IF NOT EXISTS IPL_DB;
CREATE SCHEMA IF NOT EXISTS IPL_DB.RAW;
CREATE SCHEMA IF NOT EXISTS IPL_DB.STAGING;
CREATE SCHEMA IF NOT EXISTS IPL_DB.MARTS;

CREATE ROLE IF NOT EXISTS AIRBYTE_ROLE;
CREATE ROLE IF NOT EXISTS TRANSFORM_ROLE;
CREATE ROLE IF NOT EXISTS BI_ROLE;

GRANT USAGE, OPERATE ON WAREHOUSE IPL_WH TO ROLE AIRBYTE_ROLE;
GRANT USAGE, OPERATE ON WAREHOUSE IPL_WH TO ROLE TRANSFORM_ROLE;
GRANT USAGE ON WAREHOUSE IPL_WH TO ROLE BI_ROLE;

GRANT USAGE ON DATABASE IPL_DB TO ROLE AIRBYTE_ROLE;
GRANT USAGE ON DATABASE IPL_DB TO ROLE TRANSFORM_ROLE;
GRANT USAGE ON DATABASE IPL_DB TO ROLE BI_ROLE;

GRANT ALL ON SCHEMA IPL_DB.RAW TO ROLE AIRBYTE_ROLE;
GRANT CREATE SCHEMA ON DATABASE IPL_DB TO ROLE AIRBYTE_ROLE;

GRANT USAGE ON SCHEMA IPL_DB.RAW TO ROLE TRANSFORM_ROLE;
GRANT SELECT ON ALL TABLES IN SCHEMA IPL_DB.RAW TO ROLE TRANSFORM_ROLE;
GRANT SELECT ON FUTURE TABLES IN SCHEMA IPL_DB.RAW TO ROLE TRANSFORM_ROLE;
GRANT ALL ON SCHEMA IPL_DB.STAGING TO ROLE TRANSFORM_ROLE;
GRANT ALL ON SCHEMA IPL_DB.MARTS TO ROLE TRANSFORM_ROLE;

GRANT USAGE ON SCHEMA IPL_DB.MARTS TO ROLE BI_ROLE;
GRANT SELECT ON ALL TABLES IN SCHEMA IPL_DB.MARTS TO ROLE BI_ROLE;
GRANT SELECT ON FUTURE TABLES IN SCHEMA IPL_DB.MARTS TO ROLE BI_ROLE;
GRANT SELECT ON ALL VIEWS IN SCHEMA IPL_DB.MARTS TO ROLE BI_ROLE;
GRANT SELECT ON FUTURE VIEWS IN SCHEMA IPL_DB.MARTS TO ROLE BI_ROLE;

CREATE USER IF NOT EXISTS AIRBYTE_USER PASSWORD = '<set>' DEFAULT_ROLE = AIRBYTE_ROLE DEFAULT_WAREHOUSE = IPL_WH;
CREATE USER IF NOT EXISTS DBT_USER PASSWORD = '<set>' DEFAULT_ROLE = TRANSFORM_ROLE DEFAULT_WAREHOUSE = IPL_WH;
CREATE USER IF NOT EXISTS BI_USER PASSWORD = '<set>' DEFAULT_ROLE = BI_ROLE DEFAULT_WAREHOUSE = IPL_WH;

GRANT ROLE AIRBYTE_ROLE TO USER AIRBYTE_USER;
GRANT ROLE TRANSFORM_ROLE TO USER DBT_USER;
GRANT ROLE BI_ROLE TO USER BI_USER;
```

Acceptance: logging in as each user shows only the expected access. `BI_USER` cannot select from `RAW` or `STAGING`, and cannot write anywhere.

---

## 8. Ingestion with Airbyte (A4, A5, A6)

### 8.1 Airbyte install

- Install with `abctl local install`. Get credentials with `abctl local credentials`.
- Destination: Snowflake, database `IPL_DB`, schema `RAW`, role `AIRBYTE_ROLE`, warehouse `IPL_WH`.

### 8.2 CSV connections

- Source type: File (CSV). Provider: HTTPS. Two sources: matches and deliveries.
- Dataset: any IPL 2008 onward dataset that has a matches file and a deliveries (ball-by-ball) file, for example the "IPL Complete Dataset" family on Kaggle. Place both CSVs in a public repo and use the raw URLs.
- Stream names: `ipl_matches`, `ipl_deliveries`.
- Sync mode: Full refresh, overwrite. Schedule: manual (Airflow triggers it).
- Acceptance: row counts in `RAW` equal row counts in the CSV files.

### 8.3 Weather source (Open-Meteo Archive, custom connector)

Build in Airbyte Connector Builder (declarative manifest), export YAML to `airbyte/weather_source.yaml`.

- Base URL: `https://archive-api.open-meteo.com/v1/archive`
- Query params: `latitude`, `longitude`, `start_date`, `end_date`, `hourly=temperature_2m,relative_humidity_2m,dew_point_2m,precipitation,wind_speed_10m`, `timezone=auto`
- Open-Meteo returns parallel arrays under `hourly` (`time[]`, `temperature_2m[]`, ...), not an array of objects. Set the record selector field path to `hourly`, so each API response becomes one record holding arrays. Flattening happens in dbt (Section 10.1).
- Partition router: list of partitions, each with `venue_id`, `latitude`, `longitude`, `start_date`, `end_date`. Add `venue_id`, `start_date`, `end_date` onto each record with an AddFields transformation.
- Partition list: generated by `scripts/build_weather_partitions.py` from the matches CSV and `venue_map.csv`. One partition per venue per season, with date range from first match date minus 1 day to last match date plus 1 day at that venue in that season. Write to `airbyte/weather_partitions.json` and paste into the manifest.
- Why per venue-season: Open-Meteo counts large requests as multiple calls. Short ranges per partition keep total usage well under the free daily limit (roughly 150 partitions).
- Error handling: backoff on HTTP 429, max 5 retries.
- Stream name: `weather_hourly`. Sync mode: Full refresh, overwrite.
- Acceptance: `RAW.WEATHER_HOURLY` has one row per partition and every row has non-empty arrays of equal length.
- Fallback if Connector Builder becomes a blocker: an Airflow `PythonOperator` extracts the same API into `RAW.WEATHER_HOURLY` with the same shape. Tell the user and keep the report honest about it.

### 8.4 Seeds that A builds from the real data

- `scripts/build_venue_list.py`: prints distinct raw venue names from the matches CSV with match counts.
- `seeds/venue_map.csv`: `raw_venue_name,venue_id,venue_name,city,country,latitude,longitude`. Collapse duplicate spellings of the same stadium into one `venue_id`. The agent may propose coordinates, but the user must verify each one manually before merging. List unverified ones in the summary.
- `seeds/team_map.csv`: `raw_team_name,team_id,team_name,short_name`. Map renamed franchises to one `team_id` (for example Delhi Daredevils to Delhi Capitals, Kings XI Punjab to Punjab Kings, Royal Challengers Bangalore to Bengaluru, Deccan Chargers handled as its own team).

---

## 9. Orchestration with Airflow (A3, A8, A9)

### 9.1 Infrastructure

- `docker-compose.yml`: Postgres, Airflow webserver or API server, scheduler, init job, LocalExecutor.
- `Dockerfile` extends the official Airflow image and installs: `dbt-snowflake`, `apache-airflow-providers-airbyte`, `apache-airflow-providers-snowflake`, `apache-airflow-providers-http`.
- Mount `airflow/dags` and `dbt/` into the containers. `dbt` profile reads the env vars.
- Choose Airflow 3.x if the providers support it, otherwise 2.10.x. Write DAG code with imports that match the chosen version.
- Airbyte connection in Airflow: type Airbyte, host `host.docker.internal:8000`, client id and secret from `abctl local credentials`. Verify the current auth fields in the provider docs.

### 9.2 DAG `ipl_weather_pipeline`

| Task                 | Operator                               | Purpose                                                                            |
| -------------------- | -------------------------------------- | ---------------------------------------------------------------------------------- |
| `check_sources`      | HTTP sensor or `PythonOperator`        | HEAD request on both CSV URLs and an Open-Meteo ping                               |
| `sync_ipl_csv`       | `AirbyteTriggerSyncOperator`           | Triggers CSV connection                                                            |
| `sync_weather`       | `AirbyteTriggerSyncOperator`           | Triggers weather connection (runs parallel to CSV)                                 |
| `validate_raw`       | `PythonOperator` or Snowflake operator | Row count above 0 for each raw table, no null `match_id`, weather arrays non-empty |
| `dbt_deps`           | `BashOperator`                         | `dbt deps`                                                                         |
| `dbt_seed`           | `BashOperator`                         | `dbt seed`                                                                         |
| `dbt_run`            | `BashOperator`                         | `dbt run`                                                                          |
| `dbt_test`           | `BashOperator`                         | `dbt test`                                                                         |
| `refresh_bi_context` | `BashOperator`                         | Runs `bi/schema_context.py` after `dbt docs generate`                              |
| `notify_success`     | `PythonOperator`                       | Logs a run summary (row counts per mart, test results)                             |

DAG settings: `schedule` daily, `catchup=False`, `retries=2`, `retry_delay` 2 minutes, `on_failure_callback` that logs task, run id and error clearly, tags `["ipl","de-microproject"]`. For the demo the DAG is triggered manually.

Honest design note for the report: the IPL data is historical and static, so a daily schedule re-syncs the same data. The DAG is built so a new season file or a new match date range flows through unchanged, and incremental sync by match date is listed as future work.

Acceptance: a full DAG run is green end to end, all task logs readable in the Airflow UI, and a deliberate failure (wrong URL) shows retries and the failure callback.

---

## 10. Transformation with dbt

### 10.1 Staging (A7)

Materialization: views in schema `STAGING`.

- `stg_matches`: rename and cast columns, join `team_map` and `venue_map`, derive `season_year` from `match_date` (do not trust the raw season label, some datasets use values like `2007/08`), `dl_applied` from the method column, `is_super_over`, normalized `result_type` (`runs`, `wickets`, `tie`, `no_result`).
- `stg_deliveries`: cast, map teams, `is_wicket` as boolean.
- `stg_weather_hourly`: flatten the arrays. Pattern:

```sql
select
    w.venue_id,
    t.value::timestamp_ntz as observed_at,
    w.temperature_2m[t.index]::float as temperature_c,
    w.relative_humidity_2m[t.index]::float as humidity_pct,
    w.dew_point_2m[t.index]::float as dew_point_c,
    w.precipitation[t.index]::float as precipitation_mm,
    w.wind_speed_10m[t.index]::float as wind_kmh
from {{ source('raw', 'weather_hourly') }} w,
    lateral flatten(input => w.time) t
```

Adjust field access to how Airbyte actually stores the nested `hourly` object. Deduplicate on `(venue_id, observed_at)`.

Sources file `_sources.yml` with `loaded_at_field: _airbyte_extracted_at` and a freshness warn threshold of 7 days.

### 10.2 Intermediate (B2)

Materialization: views in schema `STAGING`.

- `int_innings_totals`: per match and innings, total runs, wickets, legal balls, overs, run rate, extras.
- `int_match_weather`: one row per match with weather features. Weather window: 3 hours starting at 19:00 local time (night match default). If the matches data has a reliable day/night flag, use 15:00 for day matches. Compute `avg_temp_c`, `avg_humidity_pct`, `avg_dew_point_c`, `total_precip_mm`, `avg_wind_kmh`, `dew_spread_c` (temperature minus dew point).

Known limitation to state in the report: match start times are assumed, not observed, because the source data has no reliable start time.

### 10.3 Core marts (B3)

Materialization: tables in schema `MARTS`.

- `dim_team`: `team_id`, `team_name`, `short_name`
- `dim_venue`: `venue_id`, `venue_name`, `city`, `country`, `latitude`, `longitude`
- `fct_match`: `match_id`, `season_year`, `match_date`, `venue_id`, `team1_id`, `team2_id`, `toss_winner_id`, `toss_decision`, `winner_id`, `result_type`, `result_margin`, `player_of_match`, `dl_applied`, `first_innings_team_id`, `first_innings_runs`, `first_innings_wickets`, `second_innings_runs`, `second_innings_wickets`, `chasing_team_won` (boolean, null for no result), `avg_temp_c`, `avg_humidity_pct`, `avg_dew_point_c`, `total_precip_mm`, `avg_wind_kmh`, `dew_spread_c`, `humidity_band` (`low` below 50, `medium` 50 to 70, `high` above 70), `temp_band` (`cool` below 25, `warm` 25 to 32, `hot` above 32), `dew_risk_band` (`high` when dew_spread_c is 3 or less, `medium` up to 6, `low` above 6)
- `fct_innings`: `match_id`, `innings_no`, `batting_team_id`, `bowling_team_id`, `total_runs`, `wickets`, `overs`, `run_rate`, `extras`

Rules:

- Exclude `no_result` matches from every win-percentage denominator.
- Super over matches: `winner_id` is the super over winner, and `first_innings_runs` and `second_innings_runs` refer to the regular innings.
- `dew_risk_band` is a proxy based on dew spread, say so in the column description.

### 10.4 Analytical marts (B4)

- `mart_venue_stats`: `venue_id`, `venue_name`, `matches_played`, `avg_first_innings_runs`, `chase_win_pct`, `bat_first_win_pct`, `toss_winner_match_win_pct`
- `mart_weather_impact`: grain `humidity_band`, `temp_band`, `dew_risk_band`: `matches`, `avg_first_innings_runs`, `avg_second_innings_runs`, `chase_win_pct`
- `mart_team_season`: `team_id`, `team_name`, `season_year`, `matches`, `wins`, `win_pct`, `avg_runs_scored`, `avg_runs_conceded`
- `mart_batter_season`: `batter`, `season_year`, `matches`, `runs`, `balls_faced`, `strike_rate`, `fours`, `sixes`, `dismissals`
- `mart_bowler_season`: `bowler`, `season_year`, `balls_bowled`, `overs`, `runs_conceded`, `wickets`, `economy`
- `mart_batter_weather`: `batter`, `humidity_band`, `balls_faced`, `runs`, `strike_rate`

### 10.5 Tests and docs (B5)

- Generic: `unique` and `not_null` on all primary keys, `relationships` from facts to dims, `accepted_values` for `toss_decision`, `result_type`, `humidity_band`, `temp_band`, `dew_risk_band`.
- `dbt_utils`: `expression_is_true` for `chase_win_pct between 0 and 100`, `accepted_range` for humidity 0 to 100 and temperature -10 to 55.
- Custom test `assert_innings_total_matches_deliveries.sql`: innings total in `fct_innings` equals the sum of `total_runs` from `stg_deliveries`.
- Every mart column has a plain-language description in `_marts.yml`. These descriptions feed the LLM context, so write them precisely.
- Run `dbt docs generate` and keep the lineage graph screenshot for the report.

### 10.6 Project config

- `macros/generate_schema_name.sql`:

```sql
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
```

- `dbt_project.yml`: `staging` and `intermediate` use `+schema: STAGING`, `+materialized: view`; `marts` use `+schema: MARTS`, `+materialized: table`; seeds use `+schema: STAGING`.
- `packages.yml`: `dbt-labs/dbt_utils`.
- `profiles.yml` reads every value from `env_var(...)`.

---

## 11. Conversational BI (B6, B7, B8)

### 11.1 Behavior

Streamlit chat page. User asks a question in plain English. The app:

1. Builds a prompt with the schema context and a few example question-SQL pairs.
2. Calls Gemini and asks for JSON output: `{"sql": "...", "explanation": "..."}`. If the question cannot be answered from the marts, the model returns an empty `sql` and a reason.
3. Validates the SQL with `sql_guard.py`.
4. Runs it on Snowflake with `BI_ROLE`.
5. On SQL error, retries once by sending the error text back to the model.
6. Shows: the answer in one or two plain sentences (second Gemini call on the top 20 rows), the result table, an auto chart, and the generated SQL in an expander.

### 11.2 Files

- `config.py`: loads env.
- `db.py`: Snowflake connection with `BI_ROLE`, query function with a 30 second timeout and a row limit.
- `schema_context.py`: reads dbt `manifest.json` and `catalog.json` and writes `context/schema_context.md` containing, for each mart, the table name, description, column names, types and descriptions. Fully qualified names like `IPL_DB.MARTS.FCT_MATCH`.
- `llm.py`: Gemini calls (SQL generation, retry, summary), structured JSON output, simple in-memory cache keyed by question.
- `sql_guard.py`: parse with `sqlglot` (Snowflake dialect). Reject unless exactly one statement, it is a `SELECT` or `WITH ... SELECT`, and every referenced table is in the `MARTS` allowlist. Append `LIMIT 200` if no limit exists. Return a clear error message on rejection.
- `charts.py`: one categorical plus one numeric column gives a bar chart, a date or year column plus numeric gives a line chart, otherwise table only. Use Plotly.
- `app.py`: chat UI, sidebar with data coverage (seasons, number of matches, venues from `fct_match`), sample question buttons, chat history.

### 11.3 System prompt rules for the model

- Snowflake SQL dialect only.
- Use only tables listed in the context, always fully qualified.
- Percentages are stored as 0 to 100 values.
- Always exclude `no_result` matches when computing win rates (already handled in marts, prefer marts over `fct_match` for rates).
- Add a minimum sample size filter when ranking (for example at least 20 matches for venues, at least 300 balls for batters) unless the user states otherwise.
- Never invent columns. If unsure, say the question cannot be answered.

### 11.4 Evaluation (B8)

`bi/eval/questions.yaml` has 15 entries (`question`, `gold_sql`). `run_eval.py` runs gold SQL and generated SQL, compares result sets (order-insensitive), and prints pass rate and failures. Target is 12 of 15 or better. The pass rate goes into report section 4.

Starter questions:

1. Which venue has the highest chase win rate with at least 20 matches?
2. Which venue has the highest chase win rate when humidity is high?
3. What is the average first innings score for each humidity band?
4. Does high dew risk increase the chance of a successful chase?
5. Who scored the most runs in each season?
6. Which batter has the best strike rate in high humidity with at least 300 balls faced?
7. What is each team's win percentage at Wankhede Stadium?
8. How has the share of teams choosing to field after winning the toss changed by season?
9. At which venues does winning the toss matter most?
10. What was the highest team total and what was the weather in that match?
11. Which 5 bowlers have the best economy with at least 500 balls bowled?
12. How many matches had rain recorded and how many were affected by DL?
13. What was the hottest match and who won it?
14. What is Mumbai Indians' win percentage by humidity band?
15. What is the average score in hot matches compared with cool matches?

---

## 12. Verification commands (use after each phase)

- Snowflake: `SELECT COUNT(*) FROM IPL_DB.RAW.IPL_MATCHES;` and the same for deliveries and weather.
- dbt: `dbt deps && dbt seed && dbt run && dbt test` from `dbt/ipl_dbt` (all green).
- Known-fact checks (B10): total matches per season matches the public record, number of venues equals `dim_venue`, one famous match total (for example a well-known 200 plus chase) matches `fct_innings`.
- Airflow: trigger `ipl_weather_pipeline` from the UI, all tasks green.
- BI: `python bi/eval/run_eval.py`, then `streamlit run bi/app.py` and ask 5 starter questions.

---

## 13. Phases and timeline

Phase gates: stop and ask for approval after each phase.

### Day 1 (Fri 13 Nov, today)

- **A:** A1, A2, A3 (Airflow up), A4 (Airbyte up, CSV connection working). Within about 2 hours, get `RAW.IPL_MATCHES` and `RAW.IPL_DELIVERIES` loaded (Airbyte or manual) to unblock B.
- **B:** B1, then B2 and B3 skeletons against `RAW` once available. Get Gemini API key, Streamlit skeleton with one hardcoded query working through `BI_ROLE`.

Phase 1 done when: raw tables exist, dbt connects, Streamlit shows one query result.

### Day 2 (Sat 14 Nov)

- **A:** A5 (seeds), A6 (weather connector and full sync), A7 (staging), start A8 (DAG).
- **B:** B2 to B5 (intermediate, marts, tests, docs), B6 and B7 (context builder and LLM flow).

Phase 2 done when: all three raw tables loaded, staging models green, `fct_match` has weather columns populated, text-to-SQL answers a basic question.

### Day 3 (Sun 15 Nov)

- **A:** finish A8 and A9, failure demo, README, report sections.
- **B:** B8 (eval), B10 (sanity checks), polish UI, report sections.
- **Both:** full DAG run, integration fixes, screenshots, cross-walkthrough, record a backup demo video.

Phase 3 done when: one clean end-to-end DAG run, eval at 12 of 15 or better, screenshots captured.

### Mon 16 Nov (morning)

Freeze code. Two full dry runs of the demo. Submit report and demo in the lab slot (16 or 17 Nov).

---

## 14. Demo script (about 7 minutes)

| Min  | What                                                                             | Who     |
| ---- | -------------------------------------------------------------------------------- | ------- |
| 0:00 | Problem, objective, architecture slide                                           | A       |
| 1:00 | Airbyte UI: two connections, show the custom weather connector                   | A       |
| 2:00 | Trigger the Airflow DAG, show graph, logs, and parallel syncs                    | A       |
| 3:00 | Snowflake: raw to staging to marts, row counts                                   | B       |
| 3:45 | dbt docs lineage graph, show a test result                                       | B       |
| 4:30 | Conversational BI: 3 to 4 questions live (include a chart and the generated SQL) | B       |
| 6:00 | Eval pass rate, limitations, future work                                         | A and B |
| 6:30 | Questions                                                                        | both    |

Demo safety: keep a backup video, keep a pre-warmed Snowflake warehouse (run one query before starting), keep 3 pre-tested questions with cached answers in case the Gemini API is slow.

---

## 15. Report mapping (template sections)

| Template section                    | Content                                                                                | Owner |
| ----------------------------------- | -------------------------------------------------------------------------------------- | ----- |
| Cover page, TOC                     | Use the common format given by the college                                             | A     |
| Abstract                            | 150 words: problem, stack, result                                                      | A     |
| 1. Problem Statement and Objective  | Why weather and IPL, objective sentence from the template                              | A     |
| 2. Architecture and Tech Stack      | Tool table, data flow diagram, why each tool                                           | A     |
| 3. Implementation: Ingestion        | Both Airbyte connections, weather connector design, partitioning and rate limits       | A     |
| 3. Implementation: Orchestration    | DAG graph, task table, retries, failure callback                                       | A     |
| 3. Implementation: Transformation   | Seeds, staging, intermediate, marts, tests, lineage screenshot                         | B     |
| 3. Implementation: Warehouse and BI | Schemas, roles, least privilege for BI, text-to-SQL flow, SQL guard                    | B     |
| 4. Key Results and Demo Output      | Row counts per layer, sample questions with answers and charts, eval pass rate         | B     |
| 5. Conclusion and Learning Outcomes | Learnings, limitations (assumed match start time, dew proxy, static data), future work | B     |

Screenshots to capture: Airbyte connections, Airflow DAG graph and a green run, a failed-then-retried task, Snowflake schemas, dbt lineage, dbt test output, Streamlit answering 3 questions, eval output.

Both members review the whole report once for consistency.

---

## 16. Risks and fallbacks

| Risk                                                | Fallback                                                                                                                                                                           |
| --------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Airbyte `abctl` is too heavy or fails on the laptop | Airbyte Cloud trial for ingestion, same connections                                                                                                                                |
| Connector Builder blocked or buggy                  | Airflow `PythonOperator` extractor writing `RAW.WEATHER_HOURLY` with the same shape (disclose in report)                                                                           |
| Snowflake trial or MFA issues                       | Key-pair auth. If the account is unusable, swap to BigQuery: change dbt adapter to `dbt-bigquery`, Airbyte destination to BigQuery, and `sql_guard`/prompt dialect to BigQuery SQL |
| Open-Meteo rate limit                               | Smaller partitions, retry with backoff, run weather sync once and keep the data (static historical data)                                                                           |
| Venue names do not map cleanly                      | Manual seed mapping, list unmapped venues as a failing dbt test so nothing is silently dropped                                                                                     |
| Gemini free-tier limits or latency                  | Cache answers, keep 3 pre-tested demo questions, retry once                                                                                                                        |
| Wrong SQL from the model                            | Guard, retry with error, eval set to find weak spots and add few-shot examples                                                                                                     |
| Time runs out                                       | Cut order: `mart_batter_weather`, then bowler mart, then charts. Never cut tests, the DAG, or the SQL guard                                                                        |

---

## 17. Definition of done

- [ ] Airbyte moves both CSVs and weather data into `IPL_DB.RAW`
- [ ] Airflow DAG runs green end to end and shows retries on a forced failure
- [ ] dbt run and dbt test all green, docs and lineage generated
- [ ] `fct_match` has weather columns for at least 95 percent of matches (list the rest)
- [ ] Streamlit answers at least 12 of 15 eval questions correctly, shows SQL, table and chart
- [ ] BI user is read-only on `MARTS` only
- [ ] README explains setup in under 10 commands
- [ ] Report complete in the template format, screenshots included
- [ ] Backup demo video recorded
- [ ] Each member can explain the other member's half
