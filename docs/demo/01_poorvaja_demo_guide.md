# Member A Demo and Evaluation Guide: Poorvaja Joshi

**Role**: Data Platform, Ingestion, Cloud Architecture, Infrastructure & Security  
**Student Name**: Poorvaja Joshi (Class: D12B)  
**Email**: `2024.poorvaja.joshi@ves.ac.in`  
**Project**: End-to-End IPL and Weather Data Engineering Pipeline with Conversational BI  

---

## 1. Executive Summary of Your Ownership

As Member A, you own the entire foundation of the data platform:
1. **Cloud Data Warehouse Infrastructure**: Google Cloud Platform project provisioning (`ipl-weather-analytics` in multi-region `US`), BigQuery datasets, and zero-cost Sandbox policy.
2. **Security & Identity Architecture (IAM)**: Principle of Least Privilege across 3 distinct service accounts (`airbyte-sa`, `dbt-sa`, `bi-sa`) ensuring credentials never leak into GitHub.
3. **Data Ingestion Subsystem**:
   - Extracting 1,243 historical match records and 295,732 ball-by-ball deliveries from Cricsheet archives into BigQuery `raw`.
   - Building the custom Airbyte Declarative Connector (`airbyte/weather_source.yaml`) pulling 11,088 hourly micro-climate records from Open-Meteo REST API across stadium coordinates.
4. **Warehouse Connectivity & Secret Resilience**: Developing the BigQuery database connector (`bi/db.py`) capable of parsing any Streamlit Cloud secret format without hanging on metadata servers.

---

## 2. Your Primary Code Files and What They Do

### 1. `airbyte/weather_source.yaml`
- **What it is**: An Airbyte Low-Code Declarative Connector specification.
- **Key Concepts to Explain**:
  - Uses `HttpRequester` targeting `https://archive-api.open-meteo.com/v1/archive`.
  - Configures streams with parameterized request coordinates (`latitude`, `longitude`, `start_date`, `end_date`).
  - Implements exponential backoff strategy (`factor: 2`, `max_retries: 5`) to gracefully handle external API rate limits.
  - Pulls hourly meteorological metrics: `temperature_2m`, `relative_humidity_2m`, `dew_point_2m`, `precipitation`, and `wind_speed_10m`.

### 2. `scripts/load_raw_data.py`
- **What it is**: The high-performance batch ingestion engine for BigQuery `raw`.
- **Key Concepts to Explain**:
  - Authenticates securely via `airbyte-sa.json` (Data Editor permissions strictly on `raw`).
  - Reads Cricsheet match metadata and delivery records.
  - Ingests 1,243 matches and 295,732 delivery rows into `raw.ipl_matches` and `raw.ipl_deliveries`.
  - Configures BigQuery `LoadJobConfig` with `WRITE_TRUNCATE` for idempotency and clean batch refreshes.

### 3. `bi/db.py`
- **What it is**: The robust BigQuery client connection module.
- **Key Concepts to Explain**:
  - Implements multi-tier secret discovery: checks Streamlit Secrets (`[gcp_service_account]`, `GCP_SERVICE_ACCOUNT_KEY`), environment variables, and local fallback (`secrets/bi-sa.json`).
  - Replaces escaped newlines (`\n`) in private keys to avoid PEM format decoding errors.
  - **Crucial Defense**: If credentials fail on external hosting (Streamlit Cloud on AWS), it intercepts the failure with a clear error rather than hanging for 3 seconds on Google's internal metadata server (`metadata.google.internal`).
  - Enforces `maximum_bytes_billed = 1,000,000,000` (1 GB) and a 30-second query timeout to guarantee zero compute runaway.

### 4. `bi/config.py`
- Centralized environment configuration managing `GCP_PROJECT_ID`, `BQ_LOCATION`, and `GEMINI_MODEL`.

---

## 3. What to Show on Your Screen During the Demo

### Step 1: Google Cloud BigQuery Console
1. Open [console.cloud.google.com/bigquery](https://console.cloud.google.com/bigquery).
2. Point out project `ipl-weather-analytics` in location `US`.
3. Expand dataset `raw` and click on each table to show live row counts:
   - `raw.ipl_matches`: **1,243 rows**
   - `raw.ipl_deliveries`: **295,732 rows**
   - `raw.weather_hourly`: **11,088 rows**
4. Click on `raw.weather_hourly` -> **Schema**:
   - Highlight the columns: `temperature_2m`, `relative_humidity_2m`, `dew_point_2m`, `precipitation`, `wind_speed_10m`.
   - Explain: *"These 11,088 hourly observations represent the micro-climatic surface weather at every stadium during evening match windows."*

### Step 2: Show the Service Account Security (IAM)
1. Show the `secrets/` directory structure in VS Code:
   - Mention that all keys (`airbyte-sa.json`, `dbt-sa.json`, `bi-sa.json`) are strictly in `.gitignore`.
2. Explain the Least Privilege Model:
   - `airbyte-sa`: Write access ONLY to dataset `raw`. Cannot touch `marts`.
   - `dbt-sa`: Read access to `raw`, full access to `staging` and `marts`.
   - `streamlit-bi-sa`: Read-only access to `marts`. Cannot modify any table or read raw staging tables.

### Step 3: Show the Zero-Cost Cloud Controls
1. Highlight that BigQuery is running in **Sandbox Mode**:
   - Free tier includes 10 GB of storage and 1 TB of query processing per month.
   - Project cost is strictly **$0.00 (0 INR)**.
   - Billed bytes limit is programmatically hardcoded at 1 GB per query in `bi/db.py`.

---

## 4. Speaking Script: Your 2-Minute Demo Pitch

> *"Good morning/afternoon, evaluators. My name is Poorvaja Joshi, Member A of this project. My primary responsibility was designing and deploying the Cloud Data Platform, Ingestion Subsystem, and Security Infrastructure.*
>
> *Our project addresses a major gap in cricket analytics: match performance has historically been analyzed in isolation from environmental micro-climates. I engineered an automated ingestion pipeline that extracted 1,243 IPL matches and 295,732 ball deliveries from Cricsheet, alongside 11,088 hourly weather records from the Open-Meteo Historical Weather API.*
>
> *For our weather data, I created a custom Airbyte Declarative Connector that queries historical stadium coordinates, extracting air temperature, relative humidity, dew point, precipitation, and wind speed. All raw streams are landed into Google Cloud BigQuery in our 'raw' dataset.*
>
> *To guarantee enterprise security and cost control, I enforced the Principle of Least Privilege across three dedicated IAM service accounts: an ingestion account, a transformation account, and a read-only BI account. All secrets are gitignored, and queries are capped at a 1 GB scan limit within the BigQuery Free Tier sandbox, ensuring our entire pipeline runs at exactly zero infrastructure cost.*
>
> *I will now hand over to Bhoomi Singh, who will walk you through our dbt dimensional modeling and conversational BI application."*

---

## 5. Anticipated Evaluator Questions and Exact Answers

### Q1: Why did you choose Google Cloud BigQuery instead of PostgreSQL or MySQL?
**Answer**:
*"Relational OLTP databases like MySQL or PostgreSQL are row-oriented and optimized for transactional single-row writes. They degrade significantly when running analytical aggregations across 300,000 delivery rows and hourly weather records. BigQuery is a serverless, columnar OLAP data warehouse. It stores data by column, compressing repeated values and scanning only the columns requested in the query. Furthermore, BigQuery's Sandbox tier provides 1 TB of free monthly query processing, making it high-performance and zero-cost for our academic deployment."*

### Q2: Why use an ELT pattern instead of traditional ETL?
**Answer**:
*"In traditional ETL, transformations occur in a separate processing engine before data reaches the storage layer. If a transformation rule changes, you have to re-extract the source data. With ELT (Extract, Load, Transform), we load raw high-fidelity data directly into BigQuery 'raw' first. Then, using dbt, we perform all transformations in-database using BigQuery's distributed SQL engine. This preserves raw historical auditability and allows us to iterate on modeling without re-ingesting external sources."*

### Q3: How did you handle API rate limits and failures when fetching weather data?
**Answer**:
*"In our Airbyte declarative connector (`weather_source.yaml`), we configured an exponential backoff retry strategy with a multiplier factor of 2 and a maximum of 5 retries. If Open-Meteo returns HTTP 429 (Too Many Requests) or 503, the connector automatically pauses with exponential delay before retrying. Additionally, we parameterized the extractions by stadium coordinate chunks, avoiding burst traffic."*

### Q4: How is security maintained if your GitHub repository is public?
**Answer**:
*"We enforce a strict Zero-Secret Repository policy. All service account JSON keys and API credentials reside in a gitignored `secrets/` directory and `.env` file. For our deployed Streamlit Cloud application, credentials are encrypted and injected dynamically at runtime via Streamlit Secrets. Furthermore, each service account follows least-privilege IAM: our BI frontend service account has only read permissions on the `marts` dataset and cannot drop, alter, or insert data anywhere."*

### Q5: What happened when Streamlit showed `Failed to retrieve metadata.google.internal`?
**Answer**:
*"Streamlit Community Cloud is hosted on AWS, not Google Cloud. When BigQuery runs without explicit service account credentials, Google's client library tries to reach `metadata.google.internal` on Google Compute Engine, timing out after 3 seconds. I resolved this in `bi/db.py` by implementing a multi-key parser that directly reads the service account JSON from Streamlit Secrets, normalizes the private key, and provides clear runtime feedback instead of hanging on the network."*
