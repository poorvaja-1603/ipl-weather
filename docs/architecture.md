# Architecture and Data Contracts

## Overview

The project combines IPL match and delivery data from Cricsheet with hourly historical weather from Open-Meteo. Airbyte loads the source files into the BigQuery `raw` dataset. dbt builds staging views, intermediate views, and analytical tables in `staging` and `marts`. Airflow coordinates ingestion and transformation. Streamlit uses Gemini to answer questions with read-only queries against the marts.

## Data flow

```text
Cricsheet IPL CSV zip                    Open-Meteo Archive API
        |                                          |
scripts/build_cricket_csv.py         Airbyte Connector Builder
        |                                          |
        +------------------ Airbyte ---------------+
                           |
                    BigQuery `raw`
                           |
              dbt staging views and seeds
                           |
              dbt intermediate views
                           |
                dbt mart tables
                           |
              Streamlit + Gemini BI
                           ^
             Airflow orchestrates each step
```

## Cricsheet source and consolidated files

The builder reads the Cricsheet Ashwin CSV 2.4 archive. It uses the numbered `<match_id>.csv` and `<match_id>_info.csv` pairs, and skips the archive's `all_matches.csv` aggregate to prevent duplicate deliveries. Match result margins are derived from the first two innings when the information files do not include margins. Matches settled by an eliminator remain ties in the regular-innings result fields.

`data/ipl_matches.csv` columns, in order:

```text
match_id, season, match_date, venue, city, team1, team2, toss_winner,
toss_decision, winner, winner_runs, winner_wickets, outcome, eliminator,
method, player_of_match, event_name, match_number
```

`data/ipl_deliveries.csv` columns, in order:

```text
match_id, innings, over_no, ball_no, batting_team, bowling_team, batter,
non_striker, bowler, batter_runs, extra_runs, total_runs, wides, noballs,
is_legal_ball, is_wicket, dismissal_kind, player_dismissed
```

`over_no` and `ball_no` come from splitting Cricsheet's `ball` identifier as text. `total_runs` is batter runs plus extras. A delivery is legal unless it contains wides or no-balls. The refresh procedure is to download the latest archive through the builder, inspect the printed counts, commit the two CSVs, and run the pipeline.

## BigQuery and dbt layers

- `raw`: Airbyte source tables `ipl_matches`, `ipl_deliveries`, and `weather_hourly`.
- `staging`: `stg_matches`, `stg_deliveries`, and `stg_weather_hourly` views, mapping seeds, and the intermediate views.
- `marts`: team and venue dimensions, match and innings facts, and the six analytical marts.

`int_innings_totals` includes regular innings 1 and 2 only. `int_match_weather` averages the three local hourly observations beginning at 19:00 for each match date and venue. Cricsheet does not provide a dependable match start time, so this is an explicit evening-match assumption. The dew-risk band is a proxy based on the temperature minus dew point spread.

## Conversational BI

The Streamlit app builds Gemini's SQL context from dbt's `manifest.json` and `catalog.json`. The SQL guard accepts one BigQuery `SELECT` statement and restricts referenced tables to the `marts` dataset. BigQuery uses the read-only BI service account, a 30-second query timeout, a 1 GB maximum bytes billed setting, and a 200-row limit. Results are shown as a table, with a chart when the result columns support one.

## Security

- Airbyte writes to `raw` and `airbyte_internal`.
- dbt reads `raw` and writes `staging` and `marts`.
- BI can read `marts` only.
- Service account keys and `.env` are local and gitignored.
