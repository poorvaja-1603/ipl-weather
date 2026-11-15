# Technology Stack Deep-Dive and End-to-End Demo Sequence Guide

**Project**: End-to-End IPL and Weather Data Engineering Pipeline with Conversational BI  
**Team**: Poorvaja Joshi (Member A) & Bhoomi Singh (Member B)  
**Academic Year**: 2025-2026 | **Department of Computer Engineering, VESIT**  
**Live URL**: [https://ipl-weather.streamlit.app](https://ipl-weather.streamlit.app)  
**GitHub Repo**: [https://github.com/poorvaja-1603/ipl-weather](https://github.com/poorvaja-1603/ipl-weather)  

---

## Part 1: Comprehensive Technology Stack Explanation

This project implements an enterprise-grade modern data stack. Below is the technical justification for every tool used, why it was chosen, and how it fits into the architecture.

```
+-------------------+       +-----------------------+
|  Cricsheet Data   |       | Open-Meteo Weather API|
| (1,243 Matches,   |       | (11,088 Hourly Obs,   |
|  295,732 Balls)   |       |  5 Micro-metrics)     |
+---------+---------+       +-----------+-----------+
          |                             |
          +--------------+--------------+
                         |
                         v
          +-----------------------------+
          |      Airbyte & Ingestion    |  (Custom Declarative Connector,
          |    (Python Engine, Batched) |   Idempotent BigQuery Loads)
          +--------------+--------------+
                         |
                         v
+---------------------------------------------------------------+
|              Google Cloud BigQuery (US Multi-Region)          |
|                                                               |
|  [raw] dataset        ->  [staging] dataset   ->  [marts]     |
|  - ipl_matches            - stg_matches           - dim_team  |
|  - ipl_deliveries         - stg_deliveries        - dim_venue |
|  - weather_hourly         - stg_weather_hourly    - fct_match |
|                           - int_innings_totals    - fct_inn...|
|                           - int_match_weather     - mart_ve...|
+--------------------------------+------------------------------+
                                 |  (Managed by dbt Core,
                                 |   60/60 Tests Passing)
                                 v
+---------------------------------------------------------------+
|         Conversational BI Serving Layer (Streamlit Cloud)     |
|                                                               |
|  User Question                                                |
|       |                                                       |
|       v                                                       |
|  Google Gemini 2.5 Flash (Schema-Prompted LLM)                |
|       |                                                       |
|       v                                                       |
|  sqlglot AST SQL Guardrail (Read-only SELECT, 1GB Max Billed) |
|       |                                                       |
|       v                                                       |
|  BigQuery Query Runner (bi-sa.json, US Region)                |
|       |                                                       |
|       v                                                       |
|  Interactive Plotly Visualization + Data Table + Summary      |
+---------------------------------------------------------------+
```

---

### 1. Ingestion Layer: Airbyte Declarative Connector & Python Engine
- **What it does**: Connects to the Open-Meteo Historical Weather REST API and Cricsheet match archives, pulling raw records into BigQuery `raw`.
- **Why Airbyte was chosen**:
  - Declarative YAML specification eliminates fragile, ad-hoc Python scraping scripts.
  - Built-in schema mapping, parameter injection, and automated retry backoffs.
- **Alternatives Considered**:
  - *Custom Python Requests Script*: Quick to write but lacks standardized state management, schema evolution, and declarative connector maintainability.
  - *Fivetran*: Commercial proprietary tool; violates the academic zero-cost constraint.

### 2. Cloud Data Warehouse: Google Cloud BigQuery (Sandbox Mode)
- **What it does**: Serves as the centralized, serverless columnar OLAP data warehouse hosting our Medallion architecture (`raw`, `staging`, `marts`).
- **Why BigQuery was chosen**:
  - **Serverless & Columnar**: No infrastructure provisioning or maintenance; queries across 300,000 deliveries scan only required columns in sub-seconds.
  - **Zero-Cost Academic Sandbox**: Provides 10 GB of storage and 1 TB of query processing per month at ₹0 cost.
  - **Fine-Grained IAM**: Native support for service account role segregation (`airbyte-sa`, `dbt-sa`, `bi-sa`).
- **Alternatives Considered**:
  - *PostgreSQL / MySQL*: Row-oriented OLTP databases that struggle with analytical aggregations across hundreds of thousands of rows.
  - *Snowflake / AWS Redshift*: Require credit cards and paid cluster computing.

### 3. Analytics Engineering & Transformations: dbt Core (v1.13)
- **What it does**: Compiles modular SQL transformation models, manages dependencies as a Directed Acyclic Graph (DAG), and executes 60 automated data quality tests.
- **Why dbt Core was chosen**:
  - Enables software engineering best practices for data (version control, automated testing, documentation, modularity).
  - Pushes transformations into BigQuery's distributed compute engine (ELT pattern), avoiding data movement.
  - Built-in assertions guarantee data integrity before the BI layer accesses tables.
- **Alternatives Considered**:
  - *Stored Procedures*: Difficult to version-control, test, or debug; vendor lock-in.

### 4. Generative AI Engine: Google Gemini 2.5 Flash
- **What it does**: Translates natural language user questions into syntactically valid BigQuery GoogleSQL using schema-aware system instructions.
- **Why Gemini was chosen**:
  - Extremely fast sub-second inference latency, essential for conversational BI.
  - High SQL reasoning and strict JSON schema adherence (`response_mime_type="application/json"`).
  - Operates within free developer tier quotas.
- **Alternatives Considered**:
  - *OpenAI GPT-4o*: Requires paid API credits.
  - *Self-Hosted Open-Source LLMs (Llama 3)*: Heavy GPU memory footprint unsuitable for zero-cost serverless hosting.

### 5. Security & Validation Layer: sqlglot AST SQL Guardrail
- **What it does**: Parses generated SQL into an Abstract Syntax Tree (AST) before sending it to BigQuery.
- **Why sqlglot was chosen**:
  - Regular expressions (regex) are notoriously easy to bypass with comments or encoded syntax.
  - An AST parser mathematically evaluates the semantic grammar: guarantees that the root node is strictly a `Select` expression, checks all referenced tables against the allowed `{project}.marts` dataset, and appends a `LIMIT 200`.
- **Protection Provided**: Complete immunity against SQL injection, data exfiltration, and table modification.

### 6. Serving & Visualization: Streamlit Community Cloud & Plotly
- **What it does**: Hosts the live conversational web dashboard connected directly to the GitHub repository.
- **Why Streamlit was chosen**:
  - Python-native reactive execution with session state management.
  - Seamlessly integrates with Plotly for dynamic, responsive bar, line, and scatter charts.
  - Free cloud hosting on Streamlit Community Cloud with automatic GitHub CI/CD rebuilds.

---

## Part 2: End-to-End Data Journey (From Source to BI Visual)

| Stage | Where Data Resides | What Form it Takes | Volume / Size | Owner |
| :--- | :--- | :--- | :--- | :--- |
| **1. Sources** | Cricsheet CSVs & Open-Meteo REST API | Raw match scorecards, deliveries, and hourly weather JSON responses | 1,243 matches, 295,732 balls, 11,088 weather points | Member A |
| **2. Ingestion** | BigQuery `raw` dataset | `raw.ipl_matches`, `raw.ipl_deliveries`, `raw.weather_hourly` | Unmodified, audit-ready tables (~45 MB) | Member A |
| **3. Staging** | BigQuery `staging` dataset (dbt) | `stg_matches`, `stg_deliveries`, `stg_weather_hourly` | Cleaned dates, mapped teams, normalized metrics | Member B |
| **4. Intermediate** | BigQuery `staging` dataset (dbt) | `int_innings_totals`, `int_match_weather` | 3-hour match window (19:00-22:00), dew point spread | Member B |
| **5. Dimensional Marts** | BigQuery `marts` dataset (dbt) | `dim_venue`, `dim_team`, `fct_match`, `fct_innings`, `mart_venue_stats` | Conformed star schema with 60/60 passing tests | Member B |
| **6. Conversational BI** | Streamlit + Gemini + Plotly | GoogleSQL query -> DataFrame -> Interactive Chart + Summary | Sub-second response on live web app | Combined |

---

## Part 3: Step-by-Step Demo Sequence for Evaluators

### Setup Checklist Before You Begin (T-Minus 5 Minutes)
1. **Browser Tab 1**: Live Streamlit App -> [https://ipl-weather.streamlit.app](https://ipl-weather.streamlit.app)
2. **Browser Tab 2**: Google Cloud BigQuery Console -> Project `ipl-weather-analytics` in `US`
3. **Browser Tab 3**: GitHub Repository -> [https://github.com/poorvaja-1603/ipl-weather](https://github.com/poorvaja-1603/ipl-weather)
4. **Terminal / VS Code**: Ready in workspace `c:\Users\Poorvaja\Desktop\ipl-weather`

---

### Step 1: Introduction and Context Setting (1 Minute - Both Members)
- **Poorvaja**: *"Good morning, evaluators. Welcome to our micro project presentation: 'End-to-End IPL and Weather Data Engineering Pipeline with Conversational BI'. I am Poorvaja Joshi, Member A, responsible for the cloud data platform, ingestion engine, and security infrastructure."*
- **Bhoomi**: *"And I am Bhoomi Singh, Member B, responsible for analytics engineering with dbt Core, data quality verification, and conversational BI with Google Gemini."*
- **Poorvaja**: *"Our objective was to solve a major blind spot in sports analytics: evaluating how environmental micro-climates (such as evening dew, temperature, and humidity) influence match outcomes and chasing strategies across 17 IPL seasons, while enforcing a zero-cost cloud budget."*

---

### Step 2: Ingestion & Cloud Warehouse Architecture (2 Minutes - Poorvaja)
1. **Switch to Tab 2 (Google Cloud BigQuery Console)**.
2. Show the project: `ipl-weather-analytics` (Location: `US`).
3. Expand dataset `raw`:
   - Click `raw.ipl_matches`: point to **1,243 rows**.
   - Click `raw.ipl_deliveries`: point to **295,732 rows**.
   - Click `raw.weather_hourly`: point to **11,088 rows**.
4. Show `raw.weather_hourly` schema:
   - *"Here are the 5 meteorological metrics: air temperature at 2 meters, relative humidity, dew point, precipitation, and wind speed."*
5. Explain Ingestion Mechanics:
   - *"To extract this data, I authored a custom Airbyte Declarative Connector (`airbyte/weather_source.yaml`) that queries the Open-Meteo REST API across coordinates for all 41 IPL stadium locations with an exponential backoff retry strategy."*
6. Explain IAM & Zero-Cost Security:
   - *"All access follows the Principle of Least Privilege: `airbyte-sa` only has write permissions to `raw`, `dbt-sa` transforms data, and our frontend `bi-sa` has read-only access to `marts`. Queries operate within the BigQuery Free Sandbox with a hardcoded 1 GB scan limit."*

---

### Step 3: dbt Dimensional Modeling & 60/60 Tests (2 Minutes - Bhoomi)
1. **Switch to Terminal / VS Code**.
2. Run the dbt test suite:
   ```bash
   dbt test
   ```
3. Highlight the output:
   - Point to: **`Passed: 60 of 60 (100%)`**.
   - *"Our transformation pipeline is organized under Medallion Architecture using dbt Core. We resolve 51 historical venue aliases across 17 seasons into 41 conformed stadiums with latitude and longitude via `venue_map.csv`."*
4. Explain the Weather Modeling:
   - *"In `int_match_weather.sql`, we join match dates and coordinates with the 3-hour evening match window (19:00 to 22:00 local time). We compute the dew point spread (`temperature - dew point`) to classify matches into categorical dew risk bands."*
5. Highlight Test Rigor:
   - *"We enforce 60 automated assertions: 15 uniqueness tests, 18 not-null constraints, 12 referential foreign-key integrity tests, 10 accepted range tests, and 5 domain logic tests."*

---

### Step 4: Live Conversational BI Demo (3 Minutes - Bhoomi & Poorvaja)
1. **Switch to Tab 1 (Streamlit Live App: `ipl-weather.streamlit.app`)**.
2. Point out the sidebar:
   - Seasons: 2008 to 2024
   - Total Matches: 1,243
   - Total Venues: 36
3. **Execute Sample Question 1 (Click button)**:
   - *"Which venue has the highest chase win rate with at least 20 matches?"*
   - Show how quickly the response renders (under 1 second).
   - Click **"Generated SQL"**: Show the clean BigQuery GoogleSQL.
   - Show the interactive **Plotly Bar Chart** and data table.
   - Read the summary: *"Sawai Mansingh Stadium in Jaipur has the highest chase win rate at 64.71%."*
4. **Execute Sample Question 2 (Click button)**:
   - *"Which venue has the highest chase win rate when humidity is high?"*
   - Show the result: **MA Chidambaram Stadium in Chennai** at 62.5%, proving that moisture impedes bowling grip.
5. **Execute a Brand-New Query (Type into Chat Input)**:
   - Type: *"Which venues have the hottest average match temperature?"*
   - Press Enter.
   - Show that BigQuery executes the live analytical join across `fct_match` and `dim_venue`.
   - Show the result: **Narendra Modi Stadium in Ahmedabad** is #1 with 33.7 °C, followed by Arun Jaitley Stadium in Delhi with 31.7 °C.

---

### Step 5: Security & Injection Guardrail Demonstration (1 Minute - Bhoomi)
1. Type a destructive SQL injection into the Streamlit chat box:
   ```sql
   DROP TABLE marts.fct_match;
   ```
2. Press Enter.
3. Show the instant red error:
   > *"The SQL guard rejected the query: Only SELECT statements are permitted."*
4. Type a dataset violation query:
   ```sql
   SELECT * FROM raw.ipl_matches;
   ```
5. Press Enter.
6. Show the rejection:
   > *"The SQL guard rejected the query: Only tables in marts dataset are permitted."*
7. Explain: *"Our application uses `sqlglot` to parse the Abstract Syntax Tree (AST) before BigQuery ever sees it, providing mathematical proof of query safety."*

---

### Step 6: Sustainability & Conclusion (1 Minute - Poorvaja)
- **Poorvaja**: *"Finally, our project aligns directly with UN Sustainable Development Goals:
  - **SDG 9 (Industry, Innovation & Infrastructure)**: Modern, reproducible cloud data engineering using serverless warehouse design and AI interfaces.
  - **SDG 13 (Climate Action)**: Quantifying the empirical impact of rising temperatures and micro-climatic humidity on human athletic events.
  - **SDG 12 (Responsible Consumption)**: Zero computational waste through query byte scan caps and client caching, running at ₹0 total infrastructure cost."*
- **Both Members**: *"Thank you. We are now ready for your questions!"*
