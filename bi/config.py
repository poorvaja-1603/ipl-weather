import os
from dotenv import load_dotenv

load_dotenv()

st_secrets = {}
try:
    import streamlit as st
    st_secrets = st.secrets
except Exception:
    st_secrets = {}

def get_conf(key: str, default: str = "") -> str:
    try:
        if st_secrets and key in st_secrets:
            return str(st_secrets[key])
    except Exception:
        pass
    return os.getenv(key, default)

GCP_PROJECT_ID = get_conf("GCP_PROJECT_ID", "ipl-weather-analytics")
BQ_LOCATION = get_conf("BQ_LOCATION", "US")
GCP_KEYFILE_BI = get_conf("GCP_KEYFILE_BI", "./secrets/bi-sa.json")
BQ_MAX_BYTES_BILLED = int(get_conf("BQ_MAX_BYTES_BILLED", "1000000000"))

GEMINI_API_KEY = get_conf("GEMINI_API_KEY", "")
GEMINI_MODEL = get_conf("GEMINI_MODEL", "gemini-2.5-flash")
