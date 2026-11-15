import os
from dotenv import load_dotenv

load_dotenv()

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "ipl-weather-analytics")
BQ_LOCATION = os.getenv("BQ_LOCATION", "US")
GCP_KEYFILE_BI = os.getenv("GCP_KEYFILE_BI", "./secrets/bi-sa.json")
BQ_MAX_BYTES_BILLED = int(os.getenv("BQ_MAX_BYTES_BILLED", "1000000000"))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
