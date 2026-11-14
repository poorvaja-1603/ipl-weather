from datetime import datetime, timedelta
import os
import logging
import requests
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

def on_dag_failure(context):
    task_id = context.get('task_instance').task_id
    run_id = context.get('run_id')
    exception = context.get('exception')
    logging.error(f"Task {task_id} in run {run_id} failed: {exception}")

def check_data_sources(**context):
    matches_url = os.getenv('IPL_MATCHES_URL')
    deliveries_url = os.getenv('IPL_DELIVERIES_URL')
    weather_url = os.getenv('OPEN_METEO_ARCHIVE_URL', 'https://archive-api.open-meteo.com/v1/archive')

    logging.info("Checking data sources availability...")
    if matches_url:
        r = requests.head(matches_url, timeout=10)
        logging.info(f"Matches CSV check status: {r.status_code}")
    if deliveries_url:
        r = requests.head(deliveries_url, timeout=10)
        logging.info(f"Deliveries CSV check status: {r.status_code}")

    w = requests.get(f"{weather_url}?latitude=18.93&longitude=72.82&start_date=2024-04-01&end_date=2024-04-02&hourly=temperature_2m", timeout=10)
    logging.info(f"Open-Meteo API ping status: {w.status_code}")

def validate_raw_tables(**context):
    project_id = os.getenv('GCP_PROJECT_ID')
    keyfile = os.getenv('GCP_KEYFILE_DBT', '/opt/airflow/secrets/dbt-sa.json')

    if not os.path.exists(keyfile):
        logging.warning("GCP keyfile not found at %s. Skipping live validation in mock mode.", keyfile)
        return

    from google.cloud import bigquery
    client = bigquery.Client.from_service_account_json(keyfile, project=project_id)

    queries = {
        "matches": f"SELECT COUNT(*) as cnt FROM `{project_id}.raw.ipl_matches` WHERE match_id IS NOT NULL",
        "deliveries": f"SELECT COUNT(*) as cnt FROM `{project_id}.raw.ipl_deliveries` WHERE match_id IS NOT NULL",
        "weather": f"SELECT COUNT(*) as cnt FROM `{project_id}.raw.weather_hourly`"
    }

    for name, sql in queries.items():
        res = list(client.query(sql).result())
        cnt = res[0].cnt if res else 0
        logging.info(f"Table raw.{name} validation row count: {cnt}")
        if cnt == 0:
            raise ValueError(f"Raw table raw.{name} is empty or has null match_ids.")

def notify_pipeline_success(**context):
    logging.info("IPL Weather pipeline completed successfully on BigQuery.")

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=2),
    'on_failure_callback': on_dag_failure,
}

with DAG(
    dag_id='ipl_weather_pipeline',
    default_args=default_args,
    description='End-to-end IPL and Weather data pipeline with BigQuery',
    schedule_interval=None,  # Manual trigger for demo
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['ipl', 'de-microproject', 'bigquery'],
) as dag:

    check_sources = PythonOperator(
        task_id='check_sources',
        python_callable=check_data_sources,
    )

    sync_cricket_files = BashOperator(
        task_id='sync_cricket_files',
        bash_command='echo "Triggering Airbyte cricket files sync..."',
    )

    sync_weather = BashOperator(
        task_id='sync_weather',
        bash_command='echo "Triggering Airbyte weather sync..."',
    )

    validate_raw = PythonOperator(
        task_id='validate_raw',
        python_callable=validate_raw_tables,
    )

    dbt_deps = BashOperator(
        task_id='dbt_deps',
        bash_command='cd /opt/airflow/dbt/ipl_dbt && dbt deps',
    )

    dbt_seed = BashOperator(
        task_id='dbt_seed',
        bash_command='cd /opt/airflow/dbt/ipl_dbt && dbt seed',
    )

    dbt_run = BashOperator(
        task_id='dbt_run',
        bash_command='cd /opt/airflow/dbt/ipl_dbt && dbt run',
    )

    dbt_test = BashOperator(
        task_id='dbt_test',
        bash_command='cd /opt/airflow/dbt/ipl_dbt && dbt test',
    )

    refresh_bi_context = BashOperator(
        task_id='refresh_bi_context',
        bash_command='cd /opt/airflow/dbt/ipl_dbt && dbt docs generate && python /opt/airflow/bi/schema_context.py',
    )

    notify_success = PythonOperator(
        task_id='notify_success',
        python_callable=notify_pipeline_success,
    )

    check_sources >> [sync_cricket_files, sync_weather] >> validate_raw
    validate_raw >> dbt_deps >> dbt_seed >> dbt_run >> dbt_test >> refresh_bi_context >> notify_success
