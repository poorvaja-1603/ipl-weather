# Demo Dataset Sanity Checks

Status: the source CSV checks pass. Warehouse checks remain pending until Airbyte creates `raw.ipl_matches` and `raw.ipl_deliveries`, and Member A completes the venue mapping seed.

## Verified from the current Cricsheet archive

- Match rows: 1,243
- Delivery rows: 295,732
- Match file pairs: 1,243
- Match parse failures: 0
- Delivery CSV size: 31,760,244 bytes
- Result classification after margin derivation: 552 wins by runs, 666 wins by wickets, 16 ties, and 9 no-results

## Run after the marts build

Replace `PROJECT` with `GCP_PROJECT_ID`.

```sql
-- Match counts by season. Compare with a grouped count of data/ipl_matches.csv.
SELECT season_year, COUNT(*) AS matches
FROM `PROJECT.marts.fct_match`
GROUP BY season_year
ORDER BY season_year;

-- Confirm the venue dimension covers the venues referenced by match facts.
SELECT
  (SELECT COUNT(*) FROM `PROJECT.marts.dim_venue`) AS dimension_venues,
  (SELECT COUNT(DISTINCT venue_id) FROM `PROJECT.marts.fct_match`) AS fact_venues;

-- Inspect the highest regular innings totals and select a well-known match for a public scorecard cross-check.
SELECT match_id, innings_no, batting_team_id, total_runs, wickets
FROM `PROJECT.marts.fct_innings`
ORDER BY total_runs DESC
LIMIT 10;

-- Measure weather coverage before the demo.
SELECT
  COUNT(*) AS matches,
  COUNTIF(avg_temp_c IS NOT NULL) AS matches_with_weather,
  SAFE_DIVIDE(COUNTIF(avg_temp_c IS NOT NULL), COUNT(*)) * 100 AS weather_coverage_pct
FROM `PROJECT.marts.fct_match`;
```

Record the comparison results here after the source tables and mapping seeds are integrated. Do not claim the 95 percent weather coverage target until the last query confirms it.
