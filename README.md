# IPL + Weather Impact Pipeline

An end-to-end data engineering project that combines IPL match and ball-by-ball data with hourly historical weather. Airbyte loads source data to BigQuery, dbt builds the staging and marts layers, Airflow orchestrates the pipeline, and Streamlit provides a Gemini-powered conversational BI interface.

## Stack

- Ingestion: Airbyte for Cricsheet CSV files and the Open-Meteo Archive API
- Warehouse: BigQuery Sandbox with `raw`, `staging`, and `marts` datasets
- Transformation: dbt Core and `dbt-bigquery`
- Orchestration: Apache Airflow in Docker
- BI: Streamlit, Gemini, BigQuery, and Plotly

## Local setup

1. Create and activate a Python 3.11 environment, then install dependencies:

   ```bash
   python3.11 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env`. Add the GCP project, location, Gemini key, and service account key paths. Put the JSON keys under the gitignored `secrets/` directory.

3. Build the two Cricsheet CSV files and review the printed match count, delivery count, seasons, and file sizes:

   ```bash
   python scripts/build_cricket_csv.py
   ```

   The builder defaults to `https://cricsheet.org/downloads/ipl_csv2.zip`. To rebuild from an archive already downloaded locally, pass `--zip-path path/to/ipl_csv2.zip`.

4. Commit and push `data/ipl_matches.csv` and `data/ipl_deliveries.csv` to the configured public GitHub repository. The `.env.example` raw URLs point to this repo's `main` branch. If using another branch or repo, update `IPL_MATCHES_URL` and `IPL_DELIVERIES_URL` in `.env` before configuring Airbyte.

5. Set up Airbyte's BigQuery destination and the cricket and weather connections. Connection setup notes are in [airbyte/README.md](airbyte/README.md).

6. Run dbt from the repository root:

   ```bash
   set -a; source .env; set +a
   dbt deps --project-dir dbt/ipl_dbt --profiles-dir dbt/ipl_dbt
   dbt seed --project-dir dbt/ipl_dbt --profiles-dir dbt/ipl_dbt
   dbt run --project-dir dbt/ipl_dbt --profiles-dir dbt/ipl_dbt
   dbt test --project-dir dbt/ipl_dbt --profiles-dir dbt/ipl_dbt
   ```

7. Start Airflow and launch the BI app:

   ```bash
   docker compose up -d
   streamlit run bi/app.py
   ```

## Cricsheet refresh

Run `python scripts/build_cricket_csv.py`, review its counts and CSV sizes, commit and push the two generated CSVs, then trigger the Airflow DAG. The pipeline uses full-refresh overwrite syncs. It does not use incremental loading.

## Repository layout

- `scripts/`: source preparation utilities
- `data/`: consolidated Cricsheet CSVs
- `airbyte/`: connector notes, manifest, and weather partitions
- `airflow/`: pipeline DAG
- `dbt/ipl_dbt/`: profiles, seeds, models, tests, and docs configuration
- `bi/`: Streamlit app, Gemini flow, SQL guard, and evaluation set
- `infra/`: BigQuery setup and access grants
- `docs/`: architecture, implementation plan, and report

## Attribution

Match data from Cricsheet (cricsheet.org). Weather data from Open-Meteo.com.
