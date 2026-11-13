import os
from dotenv import load_dotenv

load_dotenv()

SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT", "")
SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE", "IPL_WH")
SNOWFLAKE_DATABASE = os.getenv("SNOWFLAKE_DATABASE", "IPL_DB")

SNOWFLAKE_BI_USER = os.getenv("SNOWFLAKE_BI_USER", "")
SNOWFLAKE_BI_PASSWORD = os.getenv("SNOWFLAKE_BI_PASSWORD", "")
SNOWFLAKE_BI_ROLE = os.getenv("SNOWFLAKE_BI_ROLE", "BI_ROLE")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
