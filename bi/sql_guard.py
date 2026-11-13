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
    "mart_batter_weather"
}

def validate_and_guard_sql(query_sql: str) -> tuple[bool, str, str]:
    if not query_sql or not query_sql.strip():
        return False, "", "Empty query."

    try:
        parsed = sqlglot.parse(query_sql, read="snowflake")
    except Exception as e:
        return False, "", f"SQL syntax error: {str(e)}"

    if len(parsed) != 1:
        return False, "", "Only a single SQL statement is allowed."

    statement = parsed[0]
    if not isinstance(statement, (exp.Select, exp.Union)):
        return False, "", "Only SELECT statements are permitted."

    tables = statement.find_all(exp.Table)
    for t in tables:
        tbl_name = t.name.lower() if t.name else ""
        db_name = t.db.lower() if t.db else ""
        catalog_name = t.catalog.lower() if t.catalog else ""

        if catalog_name and catalog_name not in ("ipl_db", ""):
            return False, "", f"Unauthorized database reference: {catalog_name}"
        if db_name and db_name not in ("marts", ""):
            return False, "", f"Only queries against MARTS schema are permitted, found: {db_name}"
        if tbl_name not in ALLOWED_MARTS_TABLES:
            return False, "", f"Unauthorized table reference: {tbl_name}. Only MARTS tables are allowed."

    # Enforce limit if not already present
    has_limit = statement.find(exp.Limit) is not None
    if not has_limit:
        statement = statement.limit(200)

    safe_sql = statement.sql(dialect="snowflake")
    return True, safe_sql, ""
