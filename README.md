# IPL + Weather Impact Pipeline

End-to-end data engineering pipeline analyzing whether weather conditions impact IPL match chase outcomes, featuring Airbyte ingestion, Snowflake data warehousing, dbt transformations, Airflow orchestration, and a conversational BI Streamlit application powered by Gemini.

## Tech Stack

- **Ingestion**: Airbyte (CSV files + Open-Meteo Archive API)
- **Warehouse**: Snowflake (Raw, Staging, Marts)
- **Transformation**: dbt Core (`dbt-snowflake`)
- **Orchestration**: Apache Airflow in Docker
- **BI Layer**: Streamlit + Gemini text-to-SQL + Plotly

## Quick Start (Setup)

1. Clone the repository and copy environment variables:
   ```bash
   cp .env.example .env
   ```
2. Configure credentials in `.env` (Snowflake, Airbyte, Gemini API key).
3. Set up Snowflake objects:
   Execute `infra/snowflake_setup.sql` in Snowflake worksheet as `ACCOUNTADMIN`.
4. Install local Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Run Airbyte and configure connections:
   See instructions in `airbyte/README.md`.
6. Start Airflow orchestration:
   ```bash
   docker compose up -d
   ```
7. Run dbt models and tests:
   ```bash
   cd dbt/ipl_dbt
   dbt deps
   dbt seed
   dbt run
   dbt test
   ```
8. Launch the Streamlit Conversational BI app:
   ```bash
   streamlit run bi/app.py
   ```

## Repository Structure

- `infra/`: Snowflake initialization scripts.
- `airbyte/`: Airbyte connector manifests and partition configs.
- `airflow/`: Airflow DAG definitions and Docker configuration.
- `scripts/`: Helper scripts for venue mapping and weather partitions.
- `dbt/ipl_dbt/`: dbt project with staging, intermediate, and marts layers.
- `bi/`: Streamlit conversational BI application with Gemini text-to-SQL and SQL guard.
- `docs/`: Architecture documentation and project reports.
