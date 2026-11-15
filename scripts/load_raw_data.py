import datetime
import json
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account

def main():
    sa_path = "secrets/airbyte-sa.json"
    with open(sa_path, "r", encoding="utf-8") as f:
        sa_data = json.load(f)

    creds = service_account.Credentials.from_service_account_info(sa_data)
    client = bigquery.Client(project="ipl-weather-analytics", credentials=creds, location="US")

    now = datetime.datetime.now(datetime.timezone.utc)

    # 1. Load ipl_matches
    print("Loading data/ipl_matches.csv into raw.ipl_matches...")
    df_matches = pd.read_csv("data/ipl_matches.csv")
    df_matches["_airbyte_extracted_at"] = now
    # Ensure types are string/numeric friendly
    df_matches["match_id"] = df_matches["match_id"].astype(int)
    for col in ["winner_runs", "winner_wickets"]:
        df_matches[col] = pd.to_numeric(df_matches[col], errors="coerce")

    table_matches = "ipl-weather-analytics.raw.ipl_matches"
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        autodetect=True,
    )
    job = client.load_table_from_dataframe(df_matches, table_matches, job_config=job_config)
    job.result()
    print(f"Successfully loaded {len(df_matches)} rows into {table_matches}")

    # 2. Load ipl_deliveries
    print("Loading data/ipl_deliveries.csv into raw.ipl_deliveries...")
    df_deliveries = pd.read_csv("data/ipl_deliveries.csv")
    df_deliveries["_airbyte_extracted_at"] = now
    df_deliveries["match_id"] = df_deliveries["match_id"].astype(int)
    for col in ["innings", "over_no", "ball_no", "batter_runs", "extra_runs", "total_runs", "wides", "noballs", "is_wicket"]:
        df_deliveries[col] = pd.to_numeric(df_deliveries[col], errors="coerce")

    table_deliveries = "ipl-weather-analytics.raw.ipl_deliveries"
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        autodetect=True,
    )
    job = client.load_table_from_dataframe(df_deliveries, table_deliveries, job_config=job_config)
    job.result()
    print(f"Successfully loaded {len(df_deliveries)} rows into {table_deliveries}")

if __name__ == "__main__":
    main()
