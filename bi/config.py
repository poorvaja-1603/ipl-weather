import os
from dotenv import load_dotenv

load_dotenv()

# Read from Streamlit secrets if running in cloud, otherwise from os.getenv
st_secrets = {}
try:
    import streamlit as st
    if hasattr(st, "secrets"):
        st_secrets = st.secrets
except Exception:
    pass

GCP_PROJECT_ID = st_secrets.get("GCP_PROJECT_ID", os.getenv("GCP_PROJECT_ID", "ipl-weather-analytics"))
BQ_LOCATION = st_secrets.get("BQ_LOCATION", os.getenv("BQ_LOCATION", "US"))
GCP_KEYFILE_BI = st_secrets.get("GCP_KEYFILE_BI", os.getenv("GCP_KEYFILE_BI", "./secrets/bi-sa.json"))
BQ_MAX_BYTES_BILLED = int(st_secrets.get("BQ_MAX_BYTES_BILLED", os.getenv("BQ_MAX_BYTES_BILLED", "1000000000")))

GEMINI_API_KEY = st_secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))
GEMINI_MODEL = st_secrets.get("GEMINI_MODEL", os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
