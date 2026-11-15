import os

import sqlglot
from sqlglot import exp


ALLOWED_MARTS_TABLES = {
    "dim_team",
    "dim_venue",
    "fct_match",
    "fct_innings",
    "mart_venue_stats",
    "mart_weather_impact",
    "mart_team_season",
    "mart_batter_season",
    "mart_bowler_season",
    "mart_batter_weather",
}


def validate_and_guard_sql(query_sql: str) -> tuple[bool, str, str]:
    if not query_sql or not query_sql.strip():
        return False, "", "Empty query."

    try:
        statements = sqlglot.parse(query_sql, read="bigquery")
    except sqlglot.errors.ParseError as error:
        return False, "", f"SQL syntax error: {error}"

    if len(statements) != 1 or statements[0] is None:
        return False, "", "Only one SQL statement is allowed."

    statement = statements[0]
    if not isinstance(statement, (exp.Select, exp.Union)):
        return False, "", "Only SELECT queries are allowed."

    project_id = os.getenv("GCP_PROJECT_ID", "").lower()
    if not project_id:
        return False, "", "GCP_PROJECT_ID must be set before running BI queries."

    cte_names = {
        cte.alias_or_name.lower()
        for cte in statement.find_all(exp.CTE)
        if cte.alias_or_name
    }
    for table in statement.find_all(exp.Table):
        table_name = (table.name or "").lower()
        if table_name in cte_names:
            continue

        dataset_name = (table.db or "").lower()
        table_project = (table.catalog or "").lower()
        if dataset_name != "marts":
            return False, "", f"Only the marts dataset is allowed, found: {dataset_name or 'unqualified table'}"
        if table_project != project_id:
            return False, "", "Every table must be fully qualified in the configured BigQuery project."
        if table_name not in ALLOWED_MARTS_TABLES:
            return False, "", f"Unauthorized marts table: {table_name}."

    if statement.args.get("limit") is None:
        statement = statement.limit(200)

    return True, statement.sql(dialect="bigquery"), ""
