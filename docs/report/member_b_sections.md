# Member B Report Sections (Working Draft)

This draft is ready to merge into the college report after the full pipeline has run. Warehouse row counts, weather coverage, BI answers, and evaluation results are intentionally left pending until the Airbyte tables and mapped venue seed are complete.

## 3. Implementation: Transformation

The Cricsheet builder consolidates the Ashwin CSV files into match-level and delivery-level tables. dbt staging models normalize the match date and result fields, map team and venue names, and flatten hourly weather arrays. Intermediate models aggregate regular innings one and two and attach a three-hour local weather window beginning at 19:00. The marts contain team and venue dimensions, match and innings facts, and venue, weather, team-season, batter-season, bowler-season, and batter-weather summaries.

dbt tests cover primary keys, foreign keys, accepted values, result percentages, source-to-map coverage, and agreement between innings runs and delivery totals. Match-start time is not included in the source data, so the evening weather window is an explicit assumption. The dew-risk grouping is a proxy based on temperature minus dew point.

## 3. Implementation: Warehouse and BI

BigQuery uses `raw`, `staging`, and `marts` datasets in one location. Airbyte writes the raw source data, dbt reads raw and writes the modeled datasets, and the BI service account is intended to have read-only access to `marts`. Streamlit sends a question and the generated dbt schema context to Gemini. The SQL guard accepts a single BigQuery `SELECT`, checks that each table is in the configured project's `marts` dataset, and adds a 200-row limit when needed. BigQuery queries also use a 30-second timeout and a 1 GB maximum bytes billed setting. The app displays generated SQL, result rows, a chart when the columns support one, and a short summary.

## 4. Key Results and Demo Output

The current Cricsheet archive produced 1,243 match rows and 295,732 delivery rows across seasons 2007/08 through 2026. The consolidated delivery CSV is approximately 31.8 MB, below GitHub's 100 MB per-file limit.

BigQuery raw and marts row counts: **pending integration**. Matches with weather observations: **pending**. BI evaluation: **not run**. Add the dbt docs lineage, test output, Streamlit examples, and evaluation output screenshots after Airbyte has loaded both cricket CSVs and the weather data.

## 5. Conclusion and Learning Outcomes

The source builder and local dbt configuration are in place. The remaining conclusions depend on a complete warehouse run. Current limitations include full-refresh loading, an assumed evening match time, incomplete venue-name mappings in the shared seed, and dew risk as a temperature/dew-point proxy. Incremental loading and a match-start-time source remain future work.

## References

- Cricsheet downloads and data licence: <https://cricsheet.org/downloads/>
- Cricsheet Ashwin CSV format: <https://cricsheet.org/format/csv_ashwin/>
- Open-Meteo Historical Weather API: <https://open-meteo.com/en/docs/historical-weather-api>
- dbt documentation: <https://docs.getdbt.com/>
- BigQuery documentation: <https://cloud.google.com/bigquery/docs>
- Gemini API model list: <https://ai.google.dev/gemini-api/docs/models>
