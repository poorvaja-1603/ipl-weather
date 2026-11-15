import json
import os

import pandas as pd
import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account

from bi.config import BQ_LOCATION, BQ_MAX_BYTES_BILLED, GCP_KEYFILE_BI, GCP_PROJECT_ID


def _normalize_private_key(info: dict) -> dict:
    normalized = dict(info)
    key = normalized.get("private_key")
    if isinstance(key, str):
        normalized["private_key"] = key.replace("\\n", "\n")
    return normalized


def get_client() -> bigquery.Client:
    if not GCP_PROJECT_ID:
        raise ValueError("GCP_PROJECT_ID is not set.")

    try:
        if "gcp_service_account" in st.secrets:
            credentials = service_account.Credentials.from_service_account_info(
                _normalize_private_key(dict(st.secrets["gcp_service_account"]))
            )
            project = st.secrets.get("GCP_PROJECT_ID", GCP_PROJECT_ID)
            return bigquery.Client(project=project, credentials=credentials, location=BQ_LOCATION)
    except Exception:
        pass

    if os.path.isfile(GCP_KEYFILE_BI):
        with open(GCP_KEYFILE_BI, encoding="utf-8") as key_file:
            key_info = _normalize_private_key(json.load(key_file))
        credentials = service_account.Credentials.from_service_account_info(key_info)
        return bigquery.Client(
            project=GCP_PROJECT_ID, credentials=credentials, location=BQ_LOCATION
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
