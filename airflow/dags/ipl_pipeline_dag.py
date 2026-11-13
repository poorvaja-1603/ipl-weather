from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
import logging

def on_dag_failure(context):
    task_id = context.get('task_instance').task_id
    run_id = context.get('run_id')
    exception = context.get('exception')
    logging.error(f"Task {task_id} in run {run_id} failed: {exception}")

def check_data_sources(**context):
    logging.info("Checking availability of raw CSV URLs and Open-Meteo endpoint...")

def validate_raw_tables(**context):
    logging.info("Validating raw data counts and schema in IPL_DB.RAW...")

def notify_pipeline_success(**context):
    logging.info("IPL Weather pipeline completed successfully.")

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
    description='End-to-end IPL and Weather impact data pipeline',
    schedule_interval=None,  # Manual trigger for demo
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['ipl', 'de-microproject'],
) as dag:

    check_sources = PythonOperator(
        task_id='check_sources',
        python_callable=check_data_sources,
    )

    # In production, replace BashOperator placeholders with AirbyteTriggerSyncOperator
    sync_ipl_csv = BashOperator(
        task_id='sync_ipl_csv',
        bash_command='echo "Triggering Airbyte CSV sync..."',
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

    check_sources >> [sync_ipl_csv, sync_weather] >> validate_raw
    validate_raw >> dbt_deps >> dbt_seed >> dbt_run >> dbt_test >> refresh_bi_context >> notify_success
