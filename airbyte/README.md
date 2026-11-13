# Airbyte Ingestion Setup

## 1. Local Airbyte Installation
Install Airbyte via abctl:
```bash
abctl local install
abctl local credentials
```
Open web UI at `http://localhost:8000`.

## 2. Destination: Snowflake
- Host: `<account_id>.snowflakecomputing.com`
- Role: `AIRBYTE_ROLE`
- Warehouse: `IPL_WH`
- Database: `IPL_DB`
- Default Schema: `RAW`
- User: `AIRBYTE_USER`
- Password: password set in `infra/snowflake_setup.sql`

## 3. Connections
- **IPL CSV Source**: File source pointing to raw HTTPS URLs for matches and deliveries.
  Stream names: `ipl_matches`, `ipl_deliveries`.
  Destination schema: `RAW`.
- **Weather Source**: Custom connector built with Connector Builder using `weather_source.yaml` and `weather_partitions.json`.
  Stream name: `weather_hourly`.
  Destination schema: `RAW`.
