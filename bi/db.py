import json
import os
from typing import Any

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


def _parse_service_account_dict(val: Any) -> dict | None:
    if val is None:
        return None
    if isinstance(val, dict):
        return dict(val)
    # Streamlit secrets TOML table behaves like a mapping
    try:
        if hasattr(val, "to_dict"):
            return val.to_dict()
        if hasattr(val, "items"):
            return {k: v for k, v in val.items()}
    except Exception:
        pass
    if isinstance(val, str):
        s = val.strip()
        if s.startswith("{") and s.endswith("}"):
            try:
                parsed = json.loads(s)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                pass
    return None


def _get_service_account_credentials() -> service_account.Credentials | None:
    # 1. Check Streamlit secrets
    try:
        candidate_keys = [
            "gcp_service_account",
            "GCP_SERVICE_ACCOUNT_KEY",
            "GCP_KEYFILE_BI",
            "gcp_credentials",
            "service_account",
        ]
        for key in candidate_keys:
            if key in st.secrets:
                val = st.secrets[key]
                info = _parse_service_account_dict(val)
                if info and "private_key" in info and "client_email" in info:
                    return service_account.Credentials.from_service_account_info(
                        _normalize_private_key(info)
                    )
    except Exception:
        pass

    # 2. Check environment variable
    for env_var in ["GCP_SERVICE_ACCOUNT_KEY", "GOOGLE_APPLICATION_CREDENTIALS_JSON"]:
        val = os.getenv(env_var)
        if val:
            info = _parse_service_account_dict(val)
            if info and "private_key" in info:
                return service_account.Credentials.from_service_account_info(
                    _normalize_private_key(info)
                )

    # 3. Check local file path
    for file_path in [GCP_KEYFILE_BI, os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")]:
        if file_path and os.path.isfile(file_path):
            with open(file_path, encoding="utf-8") as key_file:
                info = json.load(key_file)
            return service_account.Credentials.from_service_account_info(
                _normalize_private_key(info)
            )

    return None


def get_client() -> bigquery.Client:
    if not GCP_PROJECT_ID:
        raise ValueError("GCP_PROJECT_ID is not set.")

    credentials = _get_service_account_credentials()
    if credentials is not None:
        return bigquery.Client(
            project=GCP_PROJECT_ID,
            credentials=credentials,
            location=BQ_LOCATION,
        )

    # If credentials are not found, do not fall back to metadata.google.internal
    # which times out on Streamlit Cloud (AWS) and produces confusing errors.
    raise RuntimeError(
        "BigQuery service account credentials not found. "
        "In Streamlit Cloud: Open App Settings -> Secrets and paste the [gcp_service_account] section. "
        "Locally: Ensure secrets/bi-sa.json is present."
    )


def run_query(sql: str, timeout_seconds: int = 30, limit: int = 200) -> pd.DataFrame:
    client = get_client()
    job_config = bigquery.QueryJobConfig(
        maximum_bytes_billed=BQ_MAX_BYTES_BILLED,
        job_timeout_ms=timeout_seconds * 1000,
    )
    query_job = client.query(sql, job_config=job_config, timeout=timeout_seconds)
    rows = query_job.result(max_results=limit, timeout=timeout_seconds)
    return rows.to_dataframe()
