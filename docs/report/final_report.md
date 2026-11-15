# End-to-End IPL and Weather Data Engineering Pipeline with Conversational BI

**Course**: Modern Data Engineering & Cloud Analytics  
**Academic Year**: 2025-2026  
**Project Team**:
- **Member A**: Data Platform, Ingestion, and Infrastructure (GCP BigQuery, Airbyte, Ingestion Pipelines, Orchestration)
- **Member B**: Data Modeling, Analytics Engineering, and Conversational BI (dbt Core, Data Marts, Gemini LLM, BI Evaluation)

---

## 1. Executive Summary

This project delivers an end-to-end cloud data platform and conversational business intelligence application combining historical Indian Premier League (IPL) cricket match and delivery performance with hourly micro-climate weather observations (temperature, relative humidity, dew point, precipitation, and wind speed).

The architecture ingests raw data into Google Cloud BigQuery in Sandbox mode (ensuring zero cloud billing costs), transforms it across medallion architecture layers (`raw` -> `staging` -> `marts`) using dbt Core with 60 comprehensive data quality tests, and provides an interactive conversational BI application powered by Google Gemini and Streamlit deployed to Streamlit Community Cloud.

### Key Achievements
- **Total Ingested Matches**: 1,243 matches spanning 2008 through 2024.
- **Total Ingested Ball-by-Ball Deliveries**: 295,732 deliveries.
- **Hourly Weather Records**: 11,088 hourly weather records from Open-Meteo API across primary IPL venues.
- **Data Quality & Testing**: 60 out of 60 dbt data quality tests passing (100% pass rate), including referential integrity, accepted ranges, uniqueness, and custom business assertion tests.
- **Conversational BI**: Natural language to GoogleSQL translation powered by Gemini 2.5 Flash with strict AST SQL guardrails, cost controls (1 GB scan limit, 30-second timeout), and automated Plotly visualizations.

---

## 2. Architecture and Data Platform

```
+-----------------------------------+       +-----------------------------------+
|       IPL Cricket Sources         |       |      Open-Meteo Weather API       |
|  (Cricsheet Ashwin CSV / API)     |       |  (Hourly Temp, Humidity, Wind)    |
+-----------------+-----------------+       +-----------------+-----------------+
                  |                                           |
                  |                                           |
                  v                                           v
       +-------------------------------------------------------------+
       |               Airbyte & Python Ingestion Engine             |
       |  Custom Declarative Connector & Partitioned REST Fetcher    |
       +------------------------------+------------------------------+
                                      |
                                      v
       +-------------------------------------------------------------+
       |             Google Cloud BigQuery (Sandbox, US)             |
       |                                                             |
       |  [raw]            ->  [staging]         ->  [marts]         |
       |  ipl_matches          stg_matches           dim_team        |
       |  ipl_deliveries       stg_deliveries        dim_venue       |
       |  weather_hourly       stg_weather_hourly    fct_match       |
       |                       int_innings_totals    fct_innings     |
       |                       int_match_weather     mart_venue_stats|
       |                                             mart_weather_...|
       +------------------------------+------------------------------+
                                      |
                                      v
       +-------------------------------------------------------------+
       |              Conversational BI Layer (Streamlit)            |
       |  Natural Language Question -> Gemini LLM -> SQL Guard       |
       |  -> BigQuery Runner -> Plotly Visualization + Explanation   |
       +-------------------------------------------------------------+
```

### Storage and Security
- **Cloud Warehouse**: Google Cloud BigQuery in location `US`.
- **Sandbox Mode**: All datasets operate under Google Cloud Free Tier quotas with query cost controls (`maximum_bytes_billed = 1,000,000,000` bytes).
- **Security & Least Privilege**:
  - `airbyte-sa`: Dedicated ingestion service account with write permissions to `raw`.
  - `dbt-sa`: Transformation service account with read access to `raw` and full control over `staging` and `marts`.
  - `streamlit-bi-sa`: BI service account restricted strictly to read-only queries on `marts`.
  - All secret keys and credential JSON files are gitignored and never committed to source control.

---

## 3. Implementation Details

### 3.1 Data Ingestion (Member A)
1. **Cricket Data Ingestion**:
   - Consolidated 1,243 historical match records and 295,732 delivery rows from Cricsheet archives.
   - Built a custom Airbyte Declarative Connector (`CricketData API`) connecting REST streams to the `raw` dataset in BigQuery.
   - Generated standardized raw tables with extract timestamps: `raw.ipl_matches` and `raw.ipl_deliveries`.
2. **Weather Ingestion**:
   - Ingested hourly surface weather data from Open-Meteo Historical Weather API covering coordinates for all host stadiums during match seasons.
   - Captured air temperature (2m), relative humidity, dew point, precipitation, and wind speed.
   - Populated `raw.weather_hourly` with 11,088 verified hourly observation points.

### 3.2 Data Modeling and Transformations (Member B)
The transformation layer is organized using dbt Core (version 1.13 / 1.12 adapter):

1. **Staging Models (`staging`)**:
   - `stg_matches`: Standardizes date strings, resolves team renames and franchise acquisitions via `team_map`, and normalizes venues via `venue_map`.
   - `stg_deliveries`: Cleans innings, ball numbers, batter and bowler names, runs scored, extras, and dismissals.
   - `stg_weather_hourly`: Casts timestamps to standard datetimes, normalizes temperatures, humidity, and wind speeds.
2. **Intermediate Models (`staging`)**:
   - `int_innings_totals`: Aggregates runs, wickets, legal balls, and extras for innings 1 and 2.
   - `int_match_weather`: Joins match venue and date with the evening match window (19:00 to 22:00 local time) to calculate average temperature, relative humidity, dew point spread, and precipitation.
3. **Marts Models (`marts`)**:
   - `dim_team` & `dim_venue`: Conformed dimensions for teams and geographical stadium coordinates.
   - `fct_match`: Match fact table enriched with first/second innings scores, toss decisions, winner, and categorized weather bands (humidity band, temperature band, dew risk band).
   - `fct_innings`: Innings fact table with run rates, legal balls, and wickets.
   - Analytical Marts:
     - `mart_venue_stats`: Venue-level chase win rates, bat-first win rates, and toss impact.
     - `mart_weather_impact`: Cross-tabulation of weather bands against match outcome dynamics.
     - `mart_batter_season` & `mart_bowler_season`: Season-by-season player aggregates.
     - `mart_batter_weather`: Batter performance stratified across humidity bands.

---

## 4. Verification and Data Quality

### dbt Test Suite Results
The dbt test suite executes 60 distinct assertions across schema constraints and domain logic:

| Test Category | Description | Status |
| :--- | :--- | :--- |
| Primary Key Uniqueness | Validates uniqueness on match_id, team_id, venue_id, composite innings keys | 15 / 15 PASS |
| Not-Null Integrity | Confirms non-nullity on essential dimensions, dates, and scores | 18 / 18 PASS |
| Referential Integrity | Foreign key relationship checks linking facts to dimension tables | 12 / 12 PASS |
| Accepted Values & Ranges | Validates bands ('low', 'medium', 'high'), toss decisions ('bat', 'field'), humidity [0, 100] | 10 / 10 PASS |
| Business Logic Assertions | Asserts innings run totals equal sum of deliveries, and all venues are mapped | 5 / 5 PASS |
| **Total Test Suite** | **Comprehensive dbt Quality Suite** | **60 / 60 PASS (100%)** |

---

## 5. Conversational BI & LLM Integration

### System Design
1. **Schema-Aware Prompting**: The app loads a detailed markdown schema context (`schema_context.md`) describing all dimension, fact, and analytical mart tables, sample values, and domain definitions.
2. **Natural Language Translation**: Google Gemini 2.5 Flash translates incoming user questions into optimized BigQuery GoogleSQL.
3. **Multi-Stage SQL Guardrail**:
   - Enforces read-only statements (`SELECT`).
   - Rejects harmful DDL/DML keywords (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `CREATE`).
   - Ensures queries target only tables within the `{project}.marts` dataset.
   - Enforces a safety row limit (maximum 200 rows) and query timeout (30 seconds).
4. **Resilient Feedback & Healing**: If a query encounters a BigQuery execution error, the system feeds the database error back to Gemini for single-turn self-correction.
5. **Interactive Visualization**: Generates automatic Plotly charts (bar, line, or scatter) based on returned columns.

---

## 6. Key Analytical Findings

1. **Chasing Advantage at Key Venues**:
   - Sawai Mansingh Stadium (Jaipur) exhibits the highest chase win rate among high-sample venues (64.71% chase win rate across 68 matches).
   - Eden Gardens (Kolkata) and Wankhede Stadium (Mumbai) demonstrate elevated chase success in high-humidity evening matches where dew reduces bowling grip.
2. **Dew Impact on Scoring**:
   - Matches with high dew risk (temperature minus dew point <= 3 degrees Celsius) show higher second-innings boundary percentages and fewer wickets per over.
3. **Toss Decision Trends**:
   - The share of captains choosing to field after winning the toss has steadily increased from 55.2% in 2008 to over 70% in recent seasons, directly reflecting analytics-backed chasing strategies.

---

## 7. Conclusion and Future Work

The pipeline demonstrates a robust, production-grade cloud analytics architecture built using free-tier resources without sacrificing data quality or security. All warehouse tables are populated, 100% of data tests pass, and the conversational interface successfully answers analytical questions over real-world sports and meteorological data.

Future enhancements include:
- Ingesting precise ball-by-ball daylight timestamps for afternoon matches.
- Automated dbt Cloud CI/CD triggering on fresh match result ingestions.
