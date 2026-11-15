import os
from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
from bi.config import GCP_PROJECT_ID, BQ_LOCATION, GCP_KEYFILE_BI, BQ_MAX_BYTES_BILLED

def get_client() -> bigquery.Client:
    # 1. Check Streamlit cloud secrets first if deployed
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "gcp_service_account" in st.secrets:
            sa_info = dict(st.secrets["gcp_service_account"])
            credentials = service_account.Credentials.from_service_account_info(sa_info)
            project = st.secrets.get("GCP_PROJECT_ID", GCP_PROJECT_ID)
            return bigquery.Client(project=project, credentials=credentials, location=BQ_LOCATION)
    except Exception:
        pass

    # 2. Check local keyfile
    if os.path.exists(GCP_KEYFILE_BI):
        return bigquery.Client.from_service_account_json(
            GCP_KEYFILE_BI,
            project=GCP_PROJECT_ID,
            location=BQ_LOCATION
        )

    # 3. Default fallback
    return bigquery.Client(project=GCP_PROJECT_ID, location=BQ_LOCATION)

def run_query(sql: str, timeout_seconds: int = 30, limit: int = 200) -> pd.DataFrame:
    client = get_client()
    job_config = bigquery.QueryJobConfig(
        maximum_bytes_billed=BQ_MAX_BYTES_BILLED
    )
    query_job = client.query(sql, job_config=job_config, timeout=timeout_seconds)
    rows = query_job.result(max_results=limit)
    return rows.to_dataframe()
