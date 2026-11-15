import os

import pandas as pd
from google.cloud import bigquery

from bi.config import BQ_LOCATION, BQ_MAX_BYTES_BILLED, GCP_KEYFILE_BI, GCP_PROJECT_ID


def get_client() -> bigquery.Client:
    if not GCP_PROJECT_ID:
        raise ValueError("GCP_PROJECT_ID is not set.")
    if os.path.isfile(GCP_KEYFILE_BI):
        return bigquery.Client.from_service_account_json(
            GCP_KEYFILE_BI,
            project=GCP_PROJECT_ID,
            location=BQ_LOCATION,
        )
    return bigquery.Client(project=GCP_PROJECT_ID, location=BQ_LOCATION)


def run_query(sql: str, timeout_seconds: int = 30, limit: int = 200) -> pd.DataFrame:
    client = get_client()
    job_config = bigquery.QueryJobConfig(
        maximum_bytes_billed=BQ_MAX_BYTES_BILLED,
        job_timeout_ms=timeout_seconds * 1000,
    )
    query_job = client.query(sql, job_config=job_config, timeout=timeout_seconds)
    rows = query_job.result(max_results=limit, timeout=timeout_seconds)
    return rows.to_dataframe()
