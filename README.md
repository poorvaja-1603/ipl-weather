# IPL + Weather Impact Pipeline

End-to-end data engineering pipeline analyzing whether weather conditions impact IPL match chase outcomes, featuring Airbyte ingestion, Google BigQuery (Sandbox mode) warehousing, dbt transformations, Airflow orchestration, and a conversational BI Streamlit application powered by Gemini.

## Tech Stack

- **Ingestion**: Airbyte (Cricsheet CSV files + Open-Meteo Historical Weather API)
- **Warehouse**: Google BigQuery in Sandbox mode (raw, staging, marts datasets)
- **Transformation**: dbt Core (`dbt-bigquery`)
- **Orchestration**: Apache Airflow in Docker
- **BI Layer**: Streamlit + Gemini text-to-SQL + Plotly

## Quick Start (Setup)

1. Clone the repository and copy environment variables:
   ```bash
   cp .env.example .env
   ```
2. Configure credentials in `.env` (GCP project id, Gemini API key, service account paths).
3. Set up GCP service accounts and BigQuery datasets:
   ```bash
   bash infra/bigquery_setup.sh
   ```
   Apply dataset permissions from `infra/bigquery_grants.sql`.
4. Install local Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Consolidate Cricsheet cricket data:
   ```bash
   python scripts/build_cricket_csv.py
   ```
6. Run Airbyte and configure BigQuery destination and connections:
   See instructions in `airbyte/README.md`.
7. Start Airflow orchestration:
   ```bash
   docker compose up -d
   ```
8. Run dbt models and tests:
   ```bash
   cd dbt/ipl_dbt
   dbt deps
   dbt seed
   dbt run
   dbt test
   ```
9. Launch the Streamlit Conversational BI app:
   ```bash
   streamlit run bi/app.py
   ```

## Repository Structure

- `infra/`: BigQuery dataset creation scripts and IAM SQL grants.
- `airbyte/`: Airbyte connector manifests and partition configs.
- `airflow/`: Airflow DAG definitions and Docker configuration.
- `scripts/`: Helper scripts for venue mapping, weather partitions, and Cricsheet consolidation.
- `dbt/ipl_dbt/`: dbt project with staging, intermediate, and marts layers.
- `bi/`: Streamlit conversational BI application with Gemini text-to-SQL and SQL guard.
- `docs/`: Architecture documentation and project reports.

## Attribution

Match data from Cricsheet (cricsheet.org). Weather data from Open-Meteo.com.
