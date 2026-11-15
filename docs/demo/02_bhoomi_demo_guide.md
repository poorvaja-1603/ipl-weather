# Member B Demo and Evaluation Guide: Bhoomi Singh

**Role**: Data Modeling, Analytics Engineering, Quality Testing, Conversational BI & LLM Integration  
**Student Name**: Bhoomi Singh (Class: D12B)  
**Email**: `2024.bhoomi.singh@ves.ac.in`  
**Project**: End-to-End IPL and Weather Data Engineering Pipeline with Conversational BI  

---

## 1. Executive Summary of Your Ownership

As Member B, you own the transformation, analytical intelligence, and user-facing presentation layers:
1. **Dimensional Modeling & Medallion Architecture**: Structuring BigQuery into `staging` and `marts` datasets using dbt Core.
2. **Entity Resolution & Geo-Spatial Mapping**: Resolving 51 venue aliases across 17 IPL seasons down to 41 conformed stadiums with latitude/longitude via `venue_map.csv`.
3. **Environmental Feature Engineering**: Joining match dates with Open-Meteo hourly observations between 19:00 and 22:00 local time, computing dew point depression and dew risk proxy bands in `int_match_weather.sql`.
4. **Data Quality & Testing Suite**: Designing and passing **60 out of 60 dbt data quality tests** (100% pass rate) across schema constraints and business logic.
5. **Conversational BI Interface**: Developing the Streamlit web application powered by Google Gemini 2.5 Flash, fortified by an AST SQL Guardrail that mathematically prevents destructive SQL injection.

---

## 2. Your Primary Code Files and What They Do

### 1. `dbt/ipl_dbt/seeds/venue_map.csv` & `seeds/team_map.csv`
- **What it is**: Dimension seed tables for entity resolution.
- **Key Concepts to Explain**:
  - Across 2008 to 2024, stadium names changed frequently (e.g., "Feroz Shah Kotla" became "Arun Jaitley Stadium", and "Sardar Patel Stadium" became "Narendra Modi Stadium").
  - `venue_map.csv` maps 51 distinct historical names to standardized `venue_id`, official `venue_name`, city, country, and precise latitude and longitude.
  - `team_map.csv` standardizes franchise rebrands (e.g., Delhi Daredevils -> Delhi Capitals, Kings XI Punjab -> Punjab Kings, Royal Challengers Bangalore -> Royal Challengers Bengaluru).

### 2. Intermediate Models (`int_match_weather.sql` & `int_innings_totals.sql`)
- **What it is**: The core transformation logic combining sports and weather.
- **Key Concepts to Explain**:
  - `int_innings_totals.sql`: Aggregates 295,732 delivery rows into first and second innings totals (runs, wickets, legal balls, extras).
  - `int_match_weather.sql`: Filters `weather_hourly` to the 3-hour evening match window (19:00 to 22:00 local time) for each venue and date. Computes average temperature, humidity, dew point, wind speed, and the **dew point spread** (`avg_temp_c - avg_dew_point_c`).

### 3. Dimensional Marts (`dbt/ipl_dbt/models/marts/`)
- `dim_venue.sql` & `dim_team.sql`: Conformed dimensions.
- `fct_match.sql`: Master fact table enriched with match results, scores, and categorical bands (`humidity_band`, `temp_band`, `dew_risk_band`).
- `fct_innings.sql`: Grain of one row per innings with run rates and boundaries.
- `mart_venue_stats.sql`: Venue-level chase win rates, bat-first win rates, and toss advantage percentages.
- `mart_weather_impact.sql`: Cross-tabulation of weather bands against match scoring dynamics.
- `mart_batter_season.sql` & `mart_bowler_season.sql`: Player performance aggregates.

### 4. `bi/sql_guard.py`
- **What it is**: The Abstract Syntax Tree (AST) SQL Security Guardrail.
- **Key Concepts to Explain**:
  - Uses `sqlglot` to parse generated SQL into a semantic tree rather than fragile regex.
  - Rejects any query that is not a single `SELECT` statement (blocks `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `CREATE`).
  - Restricts table access strictly to the `{project}.marts` dataset (blocks access to `raw` or external tables).
  - Automatically appends a safety `LIMIT 200` to prevent memory exhaustion.

### 5. `bi/llm.py` & `bi/app.py`
- **What it is**: Streamlit frontend and schema-aware Gemini LLM prompting.
- **Key Concepts to Explain**:
  - Injects `context/schema_context.md` into Gemini's system prompt so it understands our exact star schema without seeing customer data.
  - Includes a single-turn self-correction loop: if BigQuery returns a syntax error, the error is fed back to Gemini to automatically correct the query.
  - Implements pre-cached gold queries for instant sub-second responses on standard questions.

---

## 3. What to Show on Your Screen During the Demo

### Step 1: dbt 60/60 Test Suite Passing
1. Open terminal and run:
   ```bash
   dbt test
   ```
2. Show the console output:
   - Point out: **`Passed: 60 of 60 (100%)`**.
   - Explain the test breakdown:
     - 15 Uniqueness tests (ensuring no duplicate match or venue IDs).
     - 18 Not-Null tests (ensuring no missing critical dimensions or dates).
     - 12 Referential Integrity relationship tests (facts correctly link to dimensions).
     - 10 Accepted Values tests (e.g., toss decision must be 'bat' or 'field', humidity between 0 and 100).
     - 5 Custom Business Assertions (asserting all venues are mapped and delivery runs equal innings totals).

### Step 2: Live Streamlit Application Demo
1. Open the live app: [https://ipl-weather.streamlit.app](https://ipl-weather.streamlit.app).
2. Point out the sidebar data coverage metrics:
   - Seasons: 2008 to 2024
   - Total Matches: 1,243
   - Total Venues: 36
3. Click the first Sample Question button:
   - *"Which venue has the highest chase win rate with at least 20 matches?"*
   - Show how quickly it returns (under 1 second).
   - Expand the **"Generated SQL"** accordion: show the clean GoogleSQL querying `marts.mart_venue_stats`.
   - Show the interactive **Plotly Bar Chart** and data table.
   - Show the natural language summary: *"Sawai Mansingh Stadium has the highest chase win rate at 64.71% among venues with at least 20 matches."*

### Step 3: Type a Novel Query
Type or paste into the chat input:
> *"Which venues have the hottest average match temperature?"*
- Show that BigQuery executes the join between `fct_match` and `dim_venue`.
- Point out the result: **Narendra Modi Stadium in Ahmedabad** is #1 at 33.7 °C, followed by Arun Jaitley Stadium at 31.7 °C.

### Step 4: Demonstrate the AST SQL Guardrail in Action
1. Type a malicious SQL injection into the chat input:
   ```sql
   DROP TABLE marts.fct_match;
   ```
2. Press Enter.
3. Show the immediate red error message from our SQL guard:
   > *"The SQL guard rejected the query: Only SELECT statements are permitted."*
4. Explain: *"Our application mathematically verifies the query's syntax tree before sending anything to BigQuery, providing complete immunity against database tampering."*

---

## 4. Speaking Script: Your 2-Minute Demo Pitch

> *"Thank you, Poorvaja. My name is Bhoomi Singh, Member B of this project. I was responsible for Analytics Engineering with dbt Core, Data Quality Verification, and Conversational BI integration.*
>
> *Once Member A landed the raw data into BigQuery, I structured our warehouse into a Medallion Architecture. In our staging layer, we resolved 51 historical venue naming variations across 17 IPL seasons using our curated venue map seed, resolving them to 41 conformed stadiums with precise geographic coordinates.*
>
> *To capture micro-climate impact, I engineered an intermediate model that calculates a 3-hour evening match window between 19:00 and 22:00 local time for each match date. This allowed us to compute the dew point depression and classify matches into categorized dew risk and humidity bands.*
>
> *To guarantee enterprise-grade data reliability, I authored a comprehensive test suite in dbt. As you can see on screen, our pipeline passes 60 out of 60 tests with a 100% success rate, verifying primary keys, foreign keys, and domain business logic.*
>
> *Finally, I integrated Google Gemini 2.5 Flash and Streamlit to create our Conversational BI dashboard. Instead of requiring complex SQL queries, users can ask questions in plain English. Every generated query is checked by our custom AST SQL guardrail, which guarantees that only read-only SELECT queries targeting our marts dataset are executed. As demonstrated, users can immediately uncover that Sawai Mansingh Stadium has a 64.7% chase win rate, and that dew risk significantly increases second-innings boundary rates."*

---

## 5. Anticipated Evaluator Questions and Exact Answers

### Q1: What is a Medallion Architecture and why did you use it?
**Answer**:
*"Medallion Architecture organizes data into three logical layers of increasing refinement: Bronze (our `raw` dataset), Silver (our `staging` and intermediate models), and Gold (our dimensional `marts`). The raw layer preserves unmodified source data for auditability. The staging layer cleanses datatypes, resolves renames, and joins weather windows. The marts layer provides pre-aggregated, business-ready star schemas optimized for fast querying by our BI application. This prevents complex business logic from being repeated across queries."*

### Q2: How did you calculate match weather if historical match start times were missing?
**Answer**:
*"In historical Cricsheet CSVs, match dates are present but precise local coin-toss timestamps vary. In Indian Premier League history, evening matches standardly commence at 19:30 or 20:00 local time. We made a domain-informed engineering decision to aggregate a 3-hour observation window from 19:00 to 22:00 local venue time in `int_match_weather.sql`. We then average temperature, humidity, and wind speed over these hours to capture the representative conditions during match play."*

### Q3: How do you define and calculate Dew Risk?
**Answer**:
*"Dew forms when ambient air temperature cools down to the dew point temperature, causing moisture to condense onto the grass. We calculate the dew point spread as: `Spread = Average Temperature - Average Dew Point`. When this spread is small (less than or equal to 3.0 degrees Celsius), the air is near saturation, indicating High Dew Risk. A spread between 3.0 and 6.0 degrees Celsius indicates Medium Dew Risk, and greater than 6.0 degrees Celsius is Low Dew Risk. High dew significantly wets the ball, making it slick and difficult for bowlers to control."*

### Q4: How do you prevent Gemini from hallucinating non-existent tables or columns?
**Answer**:
*"We employ Schema-Aware System Prompting. In `bi/llm.py`, we provide Gemini with a complete markdown schema context (`schema_context.md`) that lists all existing tables, column names, datatypes, sample values, and rules. We instruct the model to use only those columns and explicitly qualify tables with `{project}.marts`. Furthermore, our AST SQL guardrail checks that every table referenced in the query physically exists inside the `marts` dataset before the query is allowed to run."*

### Q5: How did you achieve 60/60 passing dbt tests?
**Answer**:
*"Initially, 2 tests failed because historical venue names contained subtle punctuation differences (such as commas inside quotes) and because the `accepted_values` test syntax required unquoted integers for innings numbers. I built an automated update script (`scripts/update_venue_map.py`) that mapped all 51 distinct venue aliases from the raw matches into `venue_map.csv`, resolved franchise name migrations in `team_map.csv`, and updated the dbt schema constraints with `quote: false`. Re-running `dbt test` verified 100% pass across all 60 assertions."*
