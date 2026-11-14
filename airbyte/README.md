# Airbyte Ingestion Setup (BigQuery Destination)

## 1. Local Airbyte Installation
Install Airbyte via abctl:
```bash
abctl local install
abctl local credentials
```
Open web UI at `http://localhost:8000`.

## 2. Destination: Google BigQuery
- Destination Type: **BigQuery**
- Project ID: your GCP project id (from `GCP_PROJECT_ID`)
- Dataset Location: `US` (or matching `BQ_LOCATION`)
- Default Dataset ID: `raw`
- Loading Method: **Standard (Insert / Load Job)** (Do NOT use GCS staging bucket as it requires billing)
- Authentication: Service Account Key JSON
  - Paste contents or upload `secrets/airbyte-sa.json`

## 3. Connections
- **Cricket Connection (`cricket_to_bigquery`)**:
  - Source Type: **File (CSV)**
  - Provider: **HTTPS**
  - Stream 1: `ipl_matches` (pointed to raw GitHub URL of `data/ipl_matches.csv`)
  - Stream 2: `ipl_deliveries` (pointed to raw GitHub URL of `data/ipl_deliveries.csv`)
  - Destination Dataset: `raw`
  - Sync Mode: **Full Refresh Overwrite**

- **Weather Connection (`weather_to_bigquery`)**:
  - Custom connector configured via Connector Builder using `airbyte/weather_source.yaml` and `airbyte/weather_partitions.json`.
  - Stream: `weather_hourly`
  - Destination Dataset: `raw`
  - Sync Mode: **Full Refresh Overwrite**
