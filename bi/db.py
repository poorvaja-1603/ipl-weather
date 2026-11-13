import snowflake.connector
import pandas as pd
from bi.config import (
    SNOWFLAKE_ACCOUNT,
    SNOWFLAKE_WAREHOUSE,
    SNOWFLAKE_DATABASE,
    SNOWFLAKE_BI_USER,
    SNOWFLAKE_BI_PASSWORD,
    SNOWFLAKE_BI_ROLE
)

def get_connection():
    return snowflake.connector.connect(
        account=SNOWFLAKE_ACCOUNT,
        user=SNOWFLAKE_BI_USER,
        password=SNOWFLAKE_BI_PASSWORD,
        role=SNOWFLAKE_BI_ROLE,
        warehouse=SNOWFLAKE_WAREHOUSE,
        database=SNOWFLAKE_DATABASE,
        schema="MARTS"
    )

def run_query(sql: str, timeout_seconds: int = 30, limit: int = 200) -> pd.DataFrame:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"ALTER SESSION SET STATEMENT_TIMEOUT_IN_SECONDS = {timeout_seconds}")
            cur.execute(sql)
            columns = [col[0].lower() for col in cur.description] if cur.description else []
            rows = cur.fetchmany(limit)
            return pd.DataFrame(rows, columns=columns)
