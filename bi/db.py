import os
from google.cloud import bigquery
import pandas as pd
from bi.config import GCP_PROJECT_ID, BQ_LOCATION, GCP_KEYFILE_BI, BQ_MAX_BYTES_BILLED

def get_client() -> bigquery.Client:
    if os.path.exists(GCP_KEYFILE_BI):
        return bigquery.Client.from_service_account_json(
            GCP_KEYFILE_BI,
            project=GCP_PROJECT_ID,
            location=BQ_LOCATION
        )
    return bigquery.Client(project=GCP_PROJECT_ID, location=BQ_LOCATION)

def run_query(sql: str, timeout_seconds: int = 30, limit: int = 200) -> pd.DataFrame:
    client = get_client()
    job_config = bigquery.QueryJobConfig(
        maximum_bytes_billed=BQ_MAX_BYTES_BILLED
    )
    query_job = client.query(sql, job_config=job_config, timeout=timeout_seconds)
    rows = query_job.result(max_results=limit)
    return rows.to_dataframe()
