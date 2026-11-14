# IPL + Weather Impact: End-to-End Data Pipeline (DE Microproject)

Team of 2 (Member A, Member B). Demo and submission: 16 and 17 Nov 2026 in lab sessions. Today is 13 Nov 2026, so the build window is about 3 days. Scope is deliberately tight.

Warehouse: Google BigQuery in sandbox mode (no credit card, no billing account).

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
5. Never hardcode secrets. Everything comes from `.env` and the gitignored `secrets/` folder (service account JSON keys). Never commit either.
6. Provider versions, connector UIs and auth methods change often (Airbyte API auth, Airflow 2 vs 3, BigQuery sandbox limits, Gemini model names). Check current official docs before writing config. If a step in this plan does not work as written, propose the smallest fix and tell the user. Do not silently swap technologies.
7. Inspect the real Cricsheet files and the consolidated CSV headers before writing any staging model. Column names in this plan are expected, not guaranteed.
8. Do not add Spark, Kafka, Kubernetes, Terraform or any extra tooling. The stack is fixed (Section 2).
9. Every phase must end with a runnable, verifiable state (commands in Section 12).
10. The BigQuery sandbox has restrictions (Section 7.3). Phase 0 is a smoke test that proves the stack works in the sandbox. Do not start Phase 1 until Phase 0 passes or the user picks a fallback.

---

## 1. Project summary

**Title:** Does the weather decide the chase? IPL match analytics with a conversational BI layer.

**Idea:** Join IPL ball-by-ball and match data with hourly historical weather (temperature, humidity, dew point, rain, wind) at each venue. Answer questions like "Which venue has the best chase win rate when humidity is above 70%?" through a natural language chat interface.

**Why it fits the rubric:** batch ingestion with Airbyte from two different source types (consolidated open cricket data files over HTTPS, and the Open-Meteo REST API through a custom connector), Airflow DAG orchestration, dbt staging and marts with tests and docs, BigQuery as the cloud warehouse, and a conversational BI interface that converts questions to SQL.

**Report template mapping:** Section 15. **Data sources and attribution:** Section 18.

---

## 2. Final decisions (do not revisit)

| Layer          | Choice                                                               | Notes                                                                                |
| -------------- | -------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| Orchestration  | Apache Airflow in Docker (LocalExecutor + Postgres)                  | Custom image includes dbt                                                            |
| Ingestion      | Airbyte (local via `abctl`)                                          | Two connections: cricket CSV files (File source) and weather (custom REST connector) |
| Warehouse      | Google BigQuery, sandbox project                                     | Datasets `raw`, `staging`, `marts`, one location for all                             |
| Transformation | dbt Core with `dbt-bigquery`                                         | Staging, intermediate, marts, tests, docs                                            |
| BI interface   | Streamlit + Gemini text-to-SQL                                       | Read-only service account, SQL guard, byte cap, charts                               |
| Language       | Python 3.11+                                                         |                                                                                      |
| VCS            | One GitHub repo (public, so raw file URLs work), branches per member |                                                                                      |

Assume Docker Desktop is available. On Windows, use WSL2. Use a personal Google account for GCP, because college Workspace accounts often block service account key creation.

All sync modes are full refresh overwrite. There is no incremental loading in this project, and the report must not claim it. Incremental loading is listed as future work.

---

## 3. Architecture and data flow

```
Cricsheet IPL zip (many small CSV files)                 Open-Meteo Archive API (REST)
              |                                                   |
   scripts/build_cricket_csv.py                                   |
   (merge into 2 CSVs, commit to GitHub)                          |
              |                                                   |
   Airbyte File source (HTTPS raw URL)          Airbyte custom source (Connector Builder)
              |                                                   |
              +---------------------> Airbyte -------------------+
                                         |
                              BigQuery dataset  raw
                                         |
                                   dbt (staging)
                         venue_map, team_map, stg_matches,
                         stg_deliveries, stg_weather_hourly
                                         |
                              dbt intermediate (views)
                      int_innings_totals, int_match_weather
                                         |
                                 dbt (marts)
        dim_team, dim_venue, fct_match, fct_innings, mart_* tables
                                         |
                    Streamlit + Gemini (read-only bi service account)
                                         ^
          Airflow DAG orchestrates every step above end to end
```

Airflow DAG `ipl_weather_pipeline`:

```
check_sources >> [sync_cricket_files, sync_weather] >> validate_raw
>> dbt_deps >> dbt_seed >> dbt_run >> dbt_test >> refresh_bi_context >> notify_success
```

---

## 4. Team split (equal load) and folder ownership

### Member A: Platform, Ingestion, Orchestration

| #   | Task                                                                                               | Output                                                               |
| --- | -------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| A1  | Repo setup, `.env.example`, `.gitignore` (include `secrets/`), README skeleton                     | Repo                                                                 |
| A2  | GCP project, BigQuery datasets, 3 service accounts, IAM (Section 7)                                | `infra/bigquery_setup.sh`, `infra/bigquery_grants.sql`               |
| A3  | Airflow in Docker with custom image (dbt, Airbyte provider, BigQuery client)                       | `docker-compose.yml`, `Dockerfile`                                   |
| A4  | Airbyte via `abctl`, BigQuery destination, cricket CSV connection `cricket_to_bigquery`            | `airbyte/` notes                                                     |
| A5  | Venue and team mapping tables from the real data, with verified coordinates                        | `seeds/venue_map.csv`, `seeds/team_map.csv`                          |
| A6  | Weather partitions script and Airbyte Connector Builder source, connection `weather_to_bigquery`   | `scripts/build_weather_partitions.py`, `airbyte/weather_source.yaml` |
| A7  | dbt staging layer: `stg_matches`, `stg_deliveries`, `stg_weather_hourly` + sources + staging tests | `dbt/ipl_dbt/models/staging/`                                        |
| A8  | Airflow DAG with retries, sensors, failure callback, dbt tasks                                     | `airflow/dags/ipl_pipeline_dag.py`                                   |
| A9  | Raw validation checks (row counts, null keys) task                                                 | inside DAG                                                           |
| A10 | Report: cover, abstract, sections 1, 2, 3.Ingestion, 3.Orchestration                               | `docs/report/`                                                       |

### Member B: Source Data, Modeling, Marts, Conversational BI

| #   | Task                                                                                  | Output                                                                            |
| --- | ------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| B0  | Cricsheet consolidation script and the two published CSVs (Section 8.2)               | `scripts/build_cricket_csv.py`, `data/ipl_matches.csv`, `data/ipl_deliveries.csv` |
| B1  | dbt project init, `profiles.yml` via env vars, `packages.yml`, schema macro           | `dbt/ipl_dbt/`                                                                    |
| B2  | Intermediate models: `int_innings_totals`, `int_match_weather`                        | `models/intermediate/`                                                            |
| B3  | Dimensions and facts: `dim_team`, `dim_venue`, `fct_match`, `fct_innings`             | `models/marts/`                                                                   |
| B4  | Analytical marts (Section 10.4)                                                       | `models/marts/`                                                                   |
| B5  | dbt tests, descriptions on every mart column, docs generation, source freshness       | `schema.yml`, `target/` docs                                                      |
| B6  | BI context builder from dbt `manifest.json` and `catalog.json`                        | `bi/schema_context.py`                                                            |
| B7  | Streamlit app: chat, text-to-SQL with Gemini, SQL guard, retry, table, chart, summary | `bi/`                                                                             |
| B8  | Evaluation set of 15 questions with gold SQL and an eval runner                       | `bi/eval/`                                                                        |
| B9  | Report: sections 3.Transformation, 3.Warehouse and BI, 4, 5, screenshots, references  | `docs/report/`                                                                    |
| B10 | Demo dataset sanity checks (known facts verified against marts)                       | notes in `docs/`                                                                  |

### Shared

- Phase 0 sandbox smoke test (Section 13): A tests the Airbyte part, B tests the dbt part.
- Integration on Day 3, full DAG run, demo rehearsal (twice), backup demo video.
- Cross-walkthrough: each member explains the other's half to the other for 30 minutes on Day 3. Viva questions will hit both halves.

### Folder ownership (avoid merge conflicts)

| Path                                                                                                                        | Owner          |
| --------------------------------------------------------------------------------------------------------------------------- | -------------- |
| `infra/`, `airbyte/`, `airflow/`, `docker-compose.yml`, `Dockerfile`                                                        | A              |
| `scripts/build_weather_partitions.py`, `scripts/build_venue_list.py`                                                        | A              |
| `dbt/ipl_dbt/seeds/`, `dbt/ipl_dbt/models/staging/`                                                                         | A              |
| `scripts/build_cricket_csv.py`, `data/`                                                                                     | B              |
| `dbt/ipl_dbt/dbt_project.yml`, `packages.yml`, `profiles.yml`, `macros/`, `models/intermediate/`, `models/marts/`, `tests/` | B              |
| `bi/`                                                                                                                       | B              |
| `docs/report/` sections                                                                                                     | per Section 15 |

### Interface contract (so both can work in parallel)

B delivers `data/ipl_matches.csv` and `data/ipl_deliveries.csv` (pushed to GitHub) within the first 2 hours of Day 1, so A can configure Airbyte. Until then, A uses a small public sample CSV to prove the Airbyte to BigQuery path.

A delivers these BigQuery tables in dataset `raw` (written by Airbyte, or loaded manually for unblocking):

- `raw.ipl_matches` (one row per match)
- `raw.ipl_deliveries` (one row per ball)
- `raw.weather_hourly` (one row per venue-season partition, with hourly arrays, see Section 8.3)

A delivers these staging models with this exact shape:

- `stg_matches`: `match_id`, `season_year`, `match_date`, `venue_id`, `team1_id`, `team2_id`, `toss_winner_id`, `toss_decision`, `winner_id`, `result_type`, `result_margin`, `player_of_match`, `dl_applied`, `is_super_over`
- `stg_deliveries`: `match_id`, `innings_no`, `over_no`, `ball_no`, `batting_team_id`, `bowling_team_id`, `batter`, `bowler`, `batter_runs`, `extra_runs`, `total_runs`, `is_legal_ball`, `is_wicket`, `dismissal_kind`, `is_super_over_innings`
- `stg_weather_hourly`: `venue_id`, `observed_at` (local DATETIME), `temperature_c`, `humidity_pct`, `dew_point_c`, `precipitation_mm`, `wind_kmh`

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
  secrets/                       (gitignored, service account JSON keys)
  data/
    ipl_matches.csv
    ipl_deliveries.csv
  infra/
    bigquery_setup.sh
    bigquery_grants.sql
  airbyte/
    README.md
    weather_source.yaml
    weather_partitions.json
  airflow/
    dags/
      ipl_pipeline_dag.py
  scripts/
    build_cricket_csv.py
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
GCP_PROJECT_ID=
BQ_LOCATION=US

GCP_KEYFILE_AIRBYTE=./secrets/airbyte-sa.json
GCP_KEYFILE_DBT=./secrets/dbt-sa.json
GCP_KEYFILE_BI=./secrets/bi-sa.json

BQ_MAX_BYTES_BILLED=1000000000

AIRBYTE_API_URL=http://host.docker.internal:8000
AIRBYTE_CLIENT_ID=
AIRBYTE_CLIENT_SECRET=
AIRBYTE_CRICKET_CONNECTION_ID=
AIRBYTE_WEATHER_CONNECTION_ID=

CRICSHEET_ZIP_URL=https://cricsheet.org/downloads/ipl_csv2.zip
IPL_MATCHES_URL=
IPL_DELIVERIES_URL=
OPEN_METEO_ARCHIVE_URL=https://archive-api.open-meteo.com/v1/archive

GEMINI_API_KEY=
GEMINI_MODEL=
```

Notes:

- `GEMINI_MODEL`: use a currently available Flash-class model from the official docs.
- Verify `CRICSHEET_ZIP_URL` on the Cricsheet downloads page before use. The IPL CSV zip name has changed in the past.
- `IPL_MATCHES_URL` and `IPL_DELIVERIES_URL` are the raw GitHub URLs of the files in `data/`.
- In Docker, mount `secrets/` read-only and pass the in-container key paths via env vars.

---

## 7. BigQuery setup (A2)

### 7.1 Project and datasets

- Create a GCP project with a personal Google account. Do NOT enable billing. Use BigQuery sandbox mode.
- Pick one location (default `US`) and use it for every dataset, the Airbyte destination and dbt. A mismatch between dataset locations breaks cross-dataset queries.
- Datasets: `raw`, `staging`, `marts`. Airbyte also creates `airbyte_internal` for its raw tables. Create that one manually in the same location if Airbyte cannot.

`infra/bigquery_setup.sh` (run in Cloud Shell or local `gcloud` and `bq`):

```bash
#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:?set GCP_PROJECT_ID}"
LOCATION="${BQ_LOCATION:-US}"

gcloud config set project "$PROJECT_ID"

for ds in raw staging marts airbyte_internal; do
  bq --location="$LOCATION" mk --dataset --if_exists=ignore "$PROJECT_ID:$ds" 2>/dev/null || \
  bq --location="$LOCATION" mk --dataset "$PROJECT_ID:$ds" || true
done

for sa in airbyte-sa dbt-sa bi-sa; do
  gcloud iam service-accounts create "$sa" --display-name="$sa" || true
done

for sa in airbyte-sa dbt-sa bi-sa; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${sa}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/bigquery.jobUser"
done

for sa in airbyte-sa dbt-sa bi-sa; do
  gcloud iam service-accounts keys create "secrets/${sa}.json" \
    --iam-account="${sa}@${PROJECT_ID}.iam.gserviceaccount.com"
done
```

Adjust the dataset creation loop if `bq mk` flags differ in the installed version. Keep the script idempotent.

### 7.2 Dataset-level access (least privilege)

`infra/bigquery_grants.sql` (run in the BigQuery console, replace `PROJECT` with the project id):

```sql
GRANT `roles/bigquery.dataEditor` ON SCHEMA `PROJECT.raw` TO "serviceAccount:airbyte-sa@PROJECT.iam.gserviceaccount.com";
GRANT `roles/bigquery.dataEditor` ON SCHEMA `PROJECT.airbyte_internal` TO "serviceAccount:airbyte-sa@PROJECT.iam.gserviceaccount.com";

GRANT `roles/bigquery.dataViewer` ON SCHEMA `PROJECT.raw` TO "serviceAccount:dbt-sa@PROJECT.iam.gserviceaccount.com";
GRANT `roles/bigquery.dataEditor` ON SCHEMA `PROJECT.staging` TO "serviceAccount:dbt-sa@PROJECT.iam.gserviceaccount.com";
GRANT `roles/bigquery.dataEditor` ON SCHEMA `PROJECT.marts` TO "serviceAccount:dbt-sa@PROJECT.iam.gserviceaccount.com";

GRANT `roles/bigquery.dataViewer` ON SCHEMA `PROJECT.marts` TO "serviceAccount:bi-sa@PROJECT.iam.gserviceaccount.com";
```

If the sandbox rejects DCL statements, grant the same roles through the console (dataset, Share, Permissions) and note it in the README. If Airbyte needs project-level `roles/bigquery.dataEditor` to create datasets or tables, grant it to `airbyte-sa` only and note it.

Acceptance: the BI service account can query `marts` but not `raw` or `staging`, and cannot write anywhere. Test with one query per dataset.

### 7.3 Sandbox limits to respect

- Tables and partitions expire after 60 days by default. Fine for this project.
- Storage up to 10 GB and 1 TB of queries per month. Fine for this project.
- The sandbox restricts some features, notably streaming inserts and DML. Reports differ on whether load jobs are also affected. This is why Phase 0 exists.
- dbt on BigQuery builds tables with `CREATE TABLE AS SELECT` and views with `CREATE VIEW`, which are DDL, not DML. Do not use incremental models, `merge` strategies, snapshots or `insert` statements anywhere.
- `dbt seed` uses load jobs. If seeds fail in the sandbox, convert `venue_map` and `team_map` to staging models written as `select * from unnest([struct(...)])` and keep the same names and columns so `ref()` calls keep working.

---

## 8. Ingestion with Airbyte (A4, A5, A6, B0)

### 8.1 Airbyte install

- Install with `abctl local install`. Get credentials with `abctl local credentials`.
- Destination: BigQuery, project id, dataset `raw`, location from `BQ_LOCATION`, service account key from `secrets/airbyte-sa.json`. If the destination asks for a loading method, choose the standard load-job method and avoid any option that needs a GCS bucket (that needs billing).
- Check the destination version's docs for how it creates final tables. If it needs DML that the sandbox blocks, Phase 0 will show it. Report back with the exact error and the fallback options in Section 16.

### 8.2 Cricket data: Cricsheet to two consolidated CSVs (B0)

Why this step exists: Cricsheet distributes IPL data as a zip of many small files (two CSV files per match: a ball-by-ball file and an `_info` file). Airbyte's File source reads one file per stream, so the zip cannot be ingested directly.

`scripts/build_cricket_csv.py`:

1. Download `CRICSHEET_ZIP_URL` and unzip into a temp folder.
2. Read every `<id>_info.csv`. Rows look like `info,<key>,<value>`; some keys repeat (`team` appears twice, `umpire` several times). Build one row per match for `data/ipl_matches.csv` with these columns: `match_id` (from file name), `season`, `match_date` (first `date` row, as `YYYY-MM-DD`), `venue`, `city`, `team1`, `team2` (the two `team` rows in order), `toss_winner`, `toss_decision`, `winner`, `winner_runs`, `winner_wickets`, `outcome` (for example tie or no result), `eliminator` (super over winner when present), `method` (for example D/L), `player_of_match`, `event_name`, `match_number`.
3. Read every ball-by-ball file `<id>.csv` and build `data/ipl_deliveries.csv` with: `match_id`, `innings`, `over_no`, `ball_no`, `batting_team`, `bowling_team`, `batter`, `non_striker`, `bowler`, `batter_runs`, `extra_runs`, `total_runs`, `wides`, `noballs`, `is_legal_ball` (false when wides or noballs are present), `is_wicket`, `dismissal_kind`, `player_dismissed`. The `ball` column in Cricsheet is like `0.1`, `5.6`, `7.7`; split it by the decimal point as text. Do not parse it as a float.
4. Skip non-CSV files (readme, licence).
5. Print row counts, number of matches, seasons covered, and any matches that failed to parse. Fail loudly if match count in the matches file differs from the number of ball-by-ball files.
6. Output must be UTF-8, comma separated, header row, no index column.

Inspect the real files first and adapt names, since the format version can change. Document the final column list in `docs/architecture.md`.

Hosting: commit both CSVs to `data/` in the public repo. Set `IPL_MATCHES_URL` and `IPL_DELIVERIES_URL` to the raw GitHub URLs. The deliveries file is large but should stay under GitHub's 100 MB file limit. If it does not, split by season into two streams and union them in staging.

Refresh procedure (state it in the README and the report): re-run the script, commit and push, then trigger the DAG.

### 8.3 Cricket connection (A4)

- Source type: File (CSV). Provider: HTTPS. Two sources or one source with two streams, whichever the current Airbyte UI supports. Stream names `ipl_matches` and `ipl_deliveries`.
- Sync mode: Full refresh, overwrite. Schedule: manual (Airflow triggers it).
- Acceptance: row counts in `raw` equal the CSV row counts.

### 8.4 Weather source (Open-Meteo Archive, custom connector) (A6)

Build in Airbyte Connector Builder (declarative manifest), export YAML to `airbyte/weather_source.yaml`.

- Base URL: `https://archive-api.open-meteo.com/v1/archive`
- Query params: `latitude`, `longitude`, `start_date`, `end_date`, `hourly=temperature_2m,relative_humidity_2m,dew_point_2m,precipitation,wind_speed_10m`, `timezone=auto`
- Open-Meteo returns parallel arrays under `hourly` (`time[]`, `temperature_2m[]`, ...), not an array of objects. Set the record selector field path to `hourly`, so each API response becomes one record holding arrays. Flattening happens in dbt (Section 10.1).
- Partition router: list of partitions, each with `venue_id`, `latitude`, `longitude`, `start_date`, `end_date`. Add `venue_id`, `start_date`, `end_date` onto each record with an AddFields transformation.
- Partition list: generated by `scripts/build_weather_partitions.py` from `data/ipl_matches.csv` and `venue_map.csv`. One partition per venue per season, with date range from first match date minus 1 day to last match date plus 1 day at that venue in that season. Write to `airbyte/weather_partitions.json` and paste into the manifest.
- Why per venue-season: Open-Meteo counts large requests as multiple calls. Short ranges per partition keep total usage well under the free daily limit (roughly 150 partitions).
- Error handling: backoff on HTTP 429, max 5 retries.
- Stream name: `weather_hourly`. Sync mode: Full refresh, overwrite.
- Acceptance: `raw.weather_hourly` has one row per partition and every row has non-empty arrays of equal length. Check how BigQuery stored the arrays (typically as JSON or string) and record it in `airbyte/README.md`, because staging depends on it.
- Fallback if Connector Builder becomes a blocker: an Airflow `PythonOperator` extracts the same API into `raw.weather_hourly` with the same shape, using the BigQuery client and a load job. Tell the user and keep the report honest about it.

### 8.5 Mapping tables built from the real data (A5)

- `scripts/build_venue_list.py`: prints distinct raw venue names (with city and match counts) from `data/ipl_matches.csv`.
- `seeds/venue_map.csv`: `raw_venue_name,venue_id,venue_name,city,country,latitude,longitude`. Collapse duplicate spellings of the same stadium into one `venue_id`. The agent may propose coordinates, but the user must verify each one manually before merging. List unverified ones in the summary. Some seasons were played outside India (2009 in South Africa, 2014 partly and 2020 in the UAE), so `country` matters and `timezone=auto` is required for weather.
- `seeds/team_map.csv`: `raw_team_name,team_id,team_name,short_name`. Map renamed franchises to one `team_id` (for example Delhi Daredevils to Delhi Capitals, Kings XI Punjab to Punjab Kings, Royal Challengers Bangalore to Bengaluru, Rising Pune Supergiant variants, Deccan Chargers as its own team).

---

## 9. Orchestration with Airflow (A3, A8, A9)

### 9.1 Infrastructure

- `docker-compose.yml`: Postgres, Airflow webserver or API server, scheduler, init job, LocalExecutor.
- `Dockerfile` extends the official Airflow image and installs: `dbt-bigquery`, `apache-airflow-providers-airbyte`, `apache-airflow-providers-http`, `google-cloud-bigquery`.
- Mount `airflow/dags`, `dbt/` and `secrets/` (read-only) into the containers. The dbt profile reads env vars.
- Choose Airflow 3.x if the providers support it, otherwise 2.10.x. Write DAG code with imports that match the chosen version.
- Airbyte connection in Airflow: type Airbyte, host `host.docker.internal:8000`, client id and secret from `abctl local credentials`. Verify the current auth fields in the provider docs.

### 9.2 DAG `ipl_weather_pipeline`

| Task                 | Operator                              | Purpose                                                                            |
| -------------------- | ------------------------------------- | ---------------------------------------------------------------------------------- |
| `check_sources`      | HTTP sensor or `PythonOperator`       | HEAD request on both raw CSV URLs and an Open-Meteo ping                           |
| `sync_cricket_files` | `AirbyteTriggerSyncOperator`          | Triggers cricket CSV connection                                                    |
| `sync_weather`       | `AirbyteTriggerSyncOperator`          | Triggers weather connection (parallel to cricket sync)                             |
| `validate_raw`       | `PythonOperator` with BigQuery client | Row count above 0 for each raw table, no null `match_id`, weather arrays non-empty |
| `dbt_deps`           | `BashOperator`                        | `dbt deps`                                                                         |
| `dbt_seed`           | `BashOperator`                        | `dbt seed`                                                                         |
| `dbt_run`            | `BashOperator`                        | `dbt run`                                                                          |
| `dbt_test`           | `BashOperator`                        | `dbt test`                                                                         |
| `refresh_bi_context` | `BashOperator`                        | `dbt docs generate`, then `bi/schema_context.py`                                   |
| `notify_success`     | `PythonOperator`                      | Logs a run summary (row counts per mart, test results)                             |

DAG settings: `schedule` daily, `catchup=False`, `retries=2`, `retry_delay` 2 minutes, `on_failure_callback` that logs task, run id and error clearly, tags `["ipl","de-microproject"]`. For the demo the DAG is triggered manually.

Honest design note for the report: IPL data is historical and the sources are re-read in full on every run (full refresh overwrite), so a daily schedule re-syncs the same data. New matches flow through when the consolidation script is re-run and pushed. Incremental sync by match date is future work.

Acceptance: a full DAG run is green end to end, all task logs readable in the Airflow UI, and a deliberate failure (wrong URL) shows retries and the failure callback.

---

## 10. Transformation with dbt (BigQuery GoogleSQL)

### 10.1 Staging (A7)

Materialization: views in dataset `staging`.

- `stg_matches`: rename and cast columns, join `team_map` and `venue_map`, derive `season_year` from the year of `match_date` (do not trust the raw season label, Cricsheet uses values like `2007/08` and `2020/21`), `dl_applied` from `method`, `is_super_over` (true when `eliminator` is not null), normalized `result_type` (`runs` when `winner_runs` is present, `wickets` when `winner_wickets` is present, `tie`, `no_result`), `result_margin` from whichever margin exists, `winner_id` (super over winner when a tie was settled by eliminator).
- `stg_deliveries`: cast, map teams, `is_wicket` as boolean, `is_super_over_innings` true when `innings` is 3 or higher.
- `stg_weather_hourly`: flatten the arrays. Pattern, assuming Airbyte stored the arrays as JSON (adapt to the real column types):

```sql
select
    w.venue_id,
    parse_datetime('%Y-%m-%dT%H:%M', json_value(t)) as observed_at,
    safe_cast(json_value(json_query_array(w.temperature_2m)[safe_offset(i)]) as float64) as temperature_c,
    safe_cast(json_value(json_query_array(w.relative_humidity_2m)[safe_offset(i)]) as float64) as humidity_pct,
    safe_cast(json_value(json_query_array(w.dew_point_2m)[safe_offset(i)]) as float64) as dew_point_c,
    safe_cast(json_value(json_query_array(w.precipitation)[safe_offset(i)]) as float64) as precipitation_mm,
    safe_cast(json_value(json_query_array(w.wind_speed_10m)[safe_offset(i)]) as float64) as wind_kmh
from {{ source('raw', 'weather_hourly') }} as w,
    unnest(json_query_array(w.`time`)) as t with offset as i
```

If Airbyte stored them as native arrays or strings, use `unnest(w.time) as t with offset as i` and `w.temperature_2m[safe_offset(i)]` instead. Deduplicate on `(venue_id, observed_at)`.

Sources file `_sources.yml` with `loaded_at_field: _airbyte_extracted_at` and a freshness warn threshold of 7 days.

### 10.2 Intermediate (B2)

Materialization: views in dataset `staging`.

- `int_innings_totals`: per match and innings (regular innings 1 and 2 only), total runs, wickets, legal balls, overs, run rate, extras. Super over innings are excluded here and handled separately.
- `int_match_weather`: one row per match with weather features. Weather window: 3 hours starting at 19:00 local time (night match default). Cricsheet has no reliable start time, so this is an assumption. If a day/night flag can be derived, use 15:00 for day matches. Compute `avg_temp_c`, `avg_humidity_pct`, `avg_dew_point_c`, `total_precip_mm`, `avg_wind_kmh`, `dew_spread_c` (temperature minus dew point). Weather timestamps are venue local time because of `timezone=auto`.

Known limitation to state in the report: match start times are assumed, not observed.

### 10.3 Core marts (B3)

Materialization: tables in dataset `marts`.

- `dim_team`: `team_id`, `team_name`, `short_name`
- `dim_venue`: `venue_id`, `venue_name`, `city`, `country`, `latitude`, `longitude`
- `fct_match`: `match_id`, `season_year`, `match_date`, `venue_id`, `team1_id`, `team2_id`, `toss_winner_id`, `toss_decision`, `winner_id`, `result_type`, `result_margin`, `player_of_match`, `dl_applied`, `first_innings_team_id`, `first_innings_runs`, `first_innings_wickets`, `second_innings_runs`, `second_innings_wickets`, `chasing_team_won` (boolean, null for no result), `avg_temp_c`, `avg_humidity_pct`, `avg_dew_point_c`, `total_precip_mm`, `avg_wind_kmh`, `dew_spread_c`, `humidity_band` (`low` below 50, `medium` 50 to 70, `high` above 70), `temp_band` (`cool` below 25, `warm` 25 to 32, `hot` above 32), `dew_risk_band` (`high` when dew_spread_c is 3 or less, `medium` up to 6, `low` above 6)
- `fct_innings`: `match_id`, `innings_no`, `batting_team_id`, `bowling_team_id`, `total_runs`, `wickets`, `overs`, `run_rate`, `extras`

Rules:

- Exclude `no_result` matches from every win-percentage denominator.
- Super over matches: `winner_id` is the super over winner, and `first_innings_runs` and `second_innings_runs` refer to the regular innings only.
- `dew_risk_band` is a proxy based on dew spread, say so in the column description.
- Use `safe_divide` for every ratio.

### 10.4 Analytical marts (B4)

- `mart_venue_stats`: `venue_id`, `venue_name`, `matches_played`, `avg_first_innings_runs`, `chase_win_pct`, `bat_first_win_pct`, `toss_winner_match_win_pct`
- `mart_weather_impact`: grain `humidity_band`, `temp_band`, `dew_risk_band`: `matches`, `avg_first_innings_runs`, `avg_second_innings_runs`, `chase_win_pct`
- `mart_team_season`: `team_id`, `team_name`, `season_year`, `matches`, `wins`, `win_pct`, `avg_runs_scored`, `avg_runs_conceded`
- `mart_batter_season`: `batter`, `season_year`, `matches`, `runs`, `balls_faced`, `strike_rate`, `fours`, `sixes`, `dismissals`
- `mart_bowler_season`: `bowler`, `season_year`, `balls_bowled`, `overs`, `runs_conceded`, `wickets`, `economy`
- `mart_batter_weather`: `batter`, `humidity_band`, `balls_faced`, `runs`, `strike_rate`

Batter and bowler marts use regular innings only (exclude super over innings) and count only legal balls for balls faced and balls bowled.

### 10.5 Tests and docs (B5)

- Generic: `unique` and `not_null` on all primary keys, `relationships` from facts to dims, `accepted_values` for `toss_decision`, `result_type`, `humidity_band`, `temp_band`, `dew_risk_band`.
- `dbt_utils`: `expression_is_true` for `chase_win_pct between 0 and 100`, `accepted_range` for humidity 0 to 100 and temperature -10 to 55.
- Mapping coverage tests: no raw venue or team name left unmapped (a failing test that lists the missing names).
- Custom test `assert_innings_total_matches_deliveries.sql`: innings total in `fct_innings` equals the sum of `total_runs` from `stg_deliveries` for regular innings.
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

- `dbt_project.yml`: `staging` and `intermediate` use `+schema: staging`, `+materialized: view`; `marts` use `+schema: marts`, `+materialized: table`; seeds use `+schema: staging`. No incremental models.
- `packages.yml`: `dbt-labs/dbt_utils`.
- `profiles.yml`: type `bigquery`, method `service-account`, `keyfile` from `GCP_KEYFILE_DBT`, `project` from `GCP_PROJECT_ID`, `dataset` `staging`, `location` from `BQ_LOCATION`, `threads` 4, `maximum_bytes_billed` from `BQ_MAX_BYTES_BILLED`. Every value from `env_var(...)`.

---

## 11. Conversational BI (B6, B7, B8)

### 11.1 Behavior

Streamlit chat page. User asks a question in plain English. The app:

1. Builds a prompt with the schema context and a few example question-SQL pairs.
2. Calls Gemini and asks for JSON output: `{"sql": "...", "explanation": "..."}`. If the question cannot be answered from the marts, the model returns an empty `sql` and a reason.
3. Validates the SQL with `sql_guard.py`.
4. Runs it on BigQuery with the read-only BI service account.
5. On SQL error, retries once by sending the error text back to the model.
6. Shows: the answer in one or two plain sentences (second Gemini call on the top 20 rows), the result table, an auto chart, and the generated SQL in an expander.

### 11.2 Files

- `config.py`: loads env.
- `db.py`: BigQuery client from `GCP_KEYFILE_BI`, query function with a 30 second timeout, `maximum_bytes_billed` from env, and a row limit.
- `schema_context.py`: reads dbt `manifest.json` and `catalog.json` and writes `context/schema_context.md` containing, for each mart, the table name, description, column names, types and descriptions. Fully qualified names like `` `PROJECT.marts.fct_match` ``.
- `llm.py`: Gemini calls (SQL generation, retry, summary), structured JSON output, simple in-memory cache keyed by question.
- `sql_guard.py`: parse with `sqlglot` (BigQuery dialect). Reject unless exactly one statement, it is a `SELECT` or `WITH ... SELECT`, and every referenced table is in the `marts` allowlist. Append `LIMIT 200` if no limit exists. Return a clear error message on rejection.
- `charts.py`: one categorical plus one numeric column gives a bar chart, a date or year column plus numeric gives a line chart, otherwise table only. Use Plotly.
- `app.py`: chat UI, sidebar with data coverage (seasons, number of matches, venues from `fct_match`), sample question buttons, chat history.

### 11.3 System prompt rules for the model

- BigQuery GoogleSQL dialect only.
- Use only tables listed in the context, always fully qualified with backticks.
- Percentages are stored as 0 to 100 values.
- Always exclude `no_result` matches when computing win rates (already handled in marts, prefer marts over `fct_match` for rates).
- Use `SAFE_DIVIDE` for ratios.
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

- BigQuery: `SELECT COUNT(*) FROM \`PROJECT.raw.ipl_matches\`;`and the same for deliveries and weather (or`bq query --use_legacy_sql=false`).
- dbt: `dbt deps && dbt seed && dbt run && dbt test` from `dbt/ipl_dbt` (all green).
- Known-fact checks (B10): total matches per season matches the public record, number of venues equals `dim_venue`, one famous match total (for example a well-known 200 plus chase) matches `fct_innings`.
- Airflow: trigger `ipl_weather_pipeline` from the UI, all tasks green.
- BI: `python bi/eval/run_eval.py`, then `streamlit run bi/app.py` and ask 5 starter questions.

---

## 13. Phases and timeline

Phase gates: stop and ask for approval after each phase.

### Phase 0: Sandbox smoke test (first 30 to 45 minutes of Day 1)

- **A (Airbyte part):** create the GCP project and datasets (A2 basics), install Airbyte, sync one small public CSV (any small sample file over HTTPS) into `raw` with full refresh overwrite using the BigQuery destination.
- **B (dbt part):** with a manually created tiny table in `raw` (for example from the BigQuery console), run `dbt run` with one view model and one table model in `staging` and `marts`, run `dbt seed` with a 3-row CSV, and run `dbt test` with one test.
- Report which of these passed: Airbyte sync, view, table, seed, test. Record exact error messages for failures.
- Decision table:
  - All pass: continue with this plan.
  - Only seed fails: convert seeds to SQL models (Section 7.3) and continue.
  - Airbyte sync fails because of sandbox restrictions: stop and show the user the fallbacks in Section 16 before doing anything else.

### Day 1 (Fri 13 Nov, today)

- **A:** Phase 0 Airbyte part, then A1, A2 (full IAM), A3 (Airflow up), A4 (Airbyte up, cricket connection as soon as B's CSVs are pushed). Get `raw.ipl_matches` and `raw.ipl_deliveries` loaded to unblock staging.
- **B:** Phase 0 dbt part, then B0 (Cricsheet consolidation and push CSVs within about 2 hours), B1 (dbt project), Gemini API key, Streamlit skeleton with one hardcoded query working through the BI service account.

Phase 1 done when: raw cricket tables exist, dbt connects, Streamlit shows one query result.

### Day 2 (Sat 14 Nov)

- **A:** A5 (mapping tables), A6 (weather connector and full sync), A7 (staging), start A8 (DAG).
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
| 3:00 | BigQuery: raw to staging to marts datasets, row counts                           | B       |
| 3:45 | dbt docs lineage graph, show a test result                                       | B       |
| 4:30 | Conversational BI: 3 to 4 questions live (include a chart and the generated SQL) | B       |
| 6:00 | Eval pass rate, limitations, future work                                         | A and B |
| 6:30 | Questions                                                                        | both    |

Demo safety: keep a backup video, run one query before starting to warm the connection, keep 3 pre-tested questions with cached answers in case the Gemini API is slow.

---

## 15. Report mapping (template sections)

| Template section                    | Content                                                                                                            | Owner                                                 |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------- |
| Cover page, TOC                     | Use the common format given by the college                                                                         | A                                                     |
| Abstract                            | 150 words: problem, stack, result                                                                                  | A                                                     |
| 1. Problem Statement and Objective  | Why weather and IPL, objective sentence from the template                                                          | A                                                     |
| 2. Architecture and Tech Stack      | Tool table, data flow diagram, why each tool                                                                       | A                                                     |
| 3. Implementation: Ingestion        | Cricsheet consolidation, both Airbyte connections, weather connector design, partitioning and rate limits          | A (Airbyte parts), B (consolidation script paragraph) |
| 3. Implementation: Orchestration    | DAG graph, task table, retries, failure callback                                                                   | A                                                     |
| 3. Implementation: Transformation   | Mapping tables, staging, intermediate, marts, tests, lineage screenshot                                            | B                                                     |
| 3. Implementation: Warehouse and BI | Datasets, service accounts, least privilege for BI, text-to-SQL flow, SQL guard, byte cap                          | B                                                     |
| 4. Key Results and Demo Output      | Row counts per layer, sample questions with answers and charts, eval pass rate                                     | B                                                     |
| 5. Conclusion and Learning Outcomes | Learnings, limitations (assumed match start time, dew proxy, full refresh only, sandbox restrictions), future work | B                                                     |
| References                          | Section 18 list                                                                                                    | B                                                     |

Screenshots to capture: Airbyte connections, Airflow DAG graph and a green run, a failed-then-retried task, BigQuery datasets, dbt lineage, dbt test output, Streamlit answering 3 questions, eval output.

Both members review the whole report once for consistency.

---

## 16. Risks and fallbacks

| Risk                                                                                   | Fallback                                                                                                                                                                                                                                                                                                                                                                                                   |
| -------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| BigQuery sandbox blocks Airbyte's destination writes or dbt operations (Phase 0 fails) | Option 1: upgrade to the GCP free trial (needs a payment card for verification, use a teammate's or family member's). Option 2: use a local warehouse, Postgres or DuckDB in Docker, with `dbt-postgres` or `dbt-duckdb` and the matching Airbyte destination, after getting faculty approval because the template names Snowflake or BigQuery. Only the setup, profile, SQL dialect and BI client change. |
| `dbt seed` fails in sandbox                                                            | Convert seeds to SQL models with `unnest([struct(...)])`, same names and columns                                                                                                                                                                                                                                                                                                                           |
| Airbyte `abctl` is too heavy or fails on the laptop                                    | Airbyte Cloud trial for ingestion if no card is needed, otherwise a Python extractor in Airflow for both sources (disclose in report)                                                                                                                                                                                                                                                                      |
| Connector Builder blocked or buggy                                                     | Airflow `PythonOperator` extractor writing `raw.weather_hourly` with the same shape (disclose in report)                                                                                                                                                                                                                                                                                                   |
| Cricsheet format or zip name changed                                                   | Inspect the zip first, adapt `build_cricket_csv.py`, keep output columns unchanged                                                                                                                                                                                                                                                                                                                         |
| Deliveries CSV over 100 MB on GitHub                                                   | Split by season into two streams and union in staging                                                                                                                                                                                                                                                                                                                                                      |
| Open-Meteo rate limit                                                                  | Smaller partitions, retry with backoff, run weather sync once and keep the data (static historical data)                                                                                                                                                                                                                                                                                                   |
| Venue names do not map cleanly                                                         | Manual mapping, unmapped venues fail a dbt test so nothing is silently dropped                                                                                                                                                                                                                                                                                                                             |
| Gemini free-tier limits or latency                                                     | Cache answers, keep 3 pre-tested demo questions, retry once                                                                                                                                                                                                                                                                                                                                                |
| Wrong SQL from the model                                                               | Guard, retry with error, eval set to find weak spots and add few-shot examples                                                                                                                                                                                                                                                                                                                             |
| Time runs out                                                                          | Cut order: `mart_batter_weather`, then bowler mart, then charts. Never cut tests, the DAG, or the SQL guard                                                                                                                                                                                                                                                                                                |

---

## 17. Definition of done

- [ ] Phase 0 smoke test passed (or a fallback was chosen and recorded)
- [ ] Airbyte loads both cricket files and weather data into the `raw` dataset (full refresh)
- [ ] Airflow DAG runs green end to end and shows retries on a forced failure
- [ ] dbt run and dbt test all green, docs and lineage generated
- [ ] `fct_match` has weather columns for at least 95 percent of matches (list the rest)
- [ ] Streamlit answers at least 12 of 15 eval questions correctly, shows SQL, table and chart
- [ ] BI service account is read-only on `marts` only
- [ ] README explains setup in under 10 commands, including the Cricsheet refresh procedure
- [ ] Report complete in the template format, screenshots and references included
- [ ] Backup demo video recorded
- [ ] Each member can explain the other member's half

---

## 18. Data sources, licences and references (use in the report)

| Source                            | Use                                                           | Link                                                  | Terms                                                                                |
| --------------------------------- | ------------------------------------------------------------- | ----------------------------------------------------- | ------------------------------------------------------------------------------------ |
| Cricsheet                         | IPL match info and ball-by-ball data                          | https://cricsheet.org/downloads/                      | Open Data Commons Attribution License (credit Cricsheet)                             |
| Cricsheet CSV format docs         | Column meaning for the "Ashwin" CSV format                    | https://www.cricsheet.org/format/csv_ashwin/          | Documentation                                                                        |
| Open-Meteo Historical Weather API | Hourly temperature, humidity, dew point, precipitation, wind  | https://open-meteo.com/en/docs/historical-weather-api | Free for non-commercial use, attribution required (verify current terms on the site) |
| Airbyte docs                      | File source, Connector Builder, BigQuery destination, `abctl` | https://docs.airbyte.com                              | Documentation                                                                        |
| BigQuery sandbox docs             | Limits and setup                                              | https://cloud.google.com/bigquery/docs/sandbox        | Documentation                                                                        |
| dbt docs                          | dbt-bigquery adapter, tests, docs                             | https://docs.getdbt.com                               | Documentation                                                                        |
| Apache Airflow docs               | DAGs, providers                                               | https://airflow.apache.org/docs/                      | Documentation                                                                        |
| Google AI for Developers          | Gemini API                                                    | https://ai.google.dev                                 | API terms apply                                                                      |

Add an attribution line in the Streamlit footer and the report: "Match data from Cricsheet (cricsheet.org). Weather data from Open-Meteo.com."
