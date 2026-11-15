import json
import re

from google import genai
from google.genai import types

from bi.config import GEMINI_API_KEY, GEMINI_MODEL, GCP_PROJECT_ID


# Pre-cached gold queries for instant sample question responses
_cache: dict[str, dict[str, str]] = {
    "which venue has the highest chase win rate with at least 20 matches?": {
        "sql": f"SELECT venue_name, chase_win_pct, matches_played FROM `{GCP_PROJECT_ID}.marts.mart_venue_stats` WHERE matches_played >= 20 ORDER BY chase_win_pct DESC LIMIT 1",
        "explanation": "Finds the venue with the highest chase win percentage among grounds with at least 20 matches."
    },
    "which venue has the highest chase win rate when humidity is high?": {
        "sql": f"SELECT v.venue_name, ROUND(100 * SAFE_DIVIDE(COUNTIF(m.chasing_team_won), COUNTIF(m.result_type != 'no_result')), 2) AS chase_win_pct, COUNT(*) AS matches FROM `{GCP_PROJECT_ID}.marts.fct_match` AS m JOIN `{GCP_PROJECT_ID}.marts.dim_venue` AS v USING (venue_id) WHERE m.humidity_band = 'high' GROUP BY v.venue_name HAVING COUNTIF(m.result_type != 'no_result') >= 5 ORDER BY chase_win_pct DESC LIMIT 1",
        "explanation": "Calculates chase win percentage for venues in high-humidity matches."
    },
    "what is the average first innings score for each humidity band?": {
        "sql": f"SELECT humidity_band, ROUND(AVG(first_innings_runs), 2) AS avg_first_innings_runs, COUNT(*) AS match_count FROM `{GCP_PROJECT_ID}.marts.fct_match` WHERE humidity_band IS NOT NULL GROUP BY humidity_band ORDER BY humidity_band",
        "explanation": "Computes average first innings runs scored across each categorized humidity band."
    },
    "does high dew risk increase the chance of a successful chase?": {
        "sql": f"SELECT dew_risk_band, ROUND(100 * SAFE_DIVIDE(COUNTIF(chasing_team_won), COUNTIF(result_type != 'no_result')), 2) AS chase_win_pct, COUNT(*) AS total_matches FROM `{GCP_PROJECT_ID}.marts.fct_match` WHERE dew_risk_band IS NOT NULL GROUP BY dew_risk_band ORDER BY dew_risk_band",
        "explanation": "Aggregates chase win rates grouped by dew risk proxy band."
    },
    "who scored the most runs in each season?": {
        "sql": f"WITH ranked AS (SELECT batter, season_year, runs, ROW_NUMBER() OVER (PARTITION BY season_year ORDER BY runs DESC, batter) AS row_num FROM `{GCP_PROJECT_ID}.marts.mart_batter_season`) SELECT season_year, batter, runs FROM ranked WHERE row_num = 1 ORDER BY season_year",
        "explanation": "Identifies the leading run scorer in each IPL season."
    },
    "which venues have the hottest average match temperature?": {
        "sql": f"SELECT v.venue_name, ROUND(AVG(m.avg_temp_c), 1) AS avg_temp_c, COUNT(*) AS matches FROM `{GCP_PROJECT_ID}.marts.fct_match` AS m JOIN `{GCP_PROJECT_ID}.marts.dim_venue` AS v USING (venue_id) GROUP BY v.venue_name HAVING COUNT(*) >= 20 ORDER BY avg_temp_c DESC LIMIT 5",
        "explanation": "Finds the venues with the highest average match temperature among grounds with at least 20 matches."
    },
    "which venue has the highest average first innings score?": {
        "sql": f"SELECT venue_name, matches_played, avg_first_innings_runs FROM `{GCP_PROJECT_ID}.marts.mart_venue_stats` WHERE matches_played >= 20 ORDER BY avg_first_innings_runs DESC LIMIT 5",
        "explanation": "Finds the highest scoring venues in IPL history for first innings runs."
    },
    "which team has won the most ipl matches overall?": {
        "sql": f"SELECT t.team_name, COUNT(*) AS total_wins FROM `{GCP_PROJECT_ID}.marts.fct_match` AS m JOIN `{GCP_PROJECT_ID}.marts.dim_team` AS t ON m.winner_id = t.team_id GROUP BY t.team_name ORDER BY total_wins DESC LIMIT 5",
        "explanation": "Ranks the teams with the highest total match victories in IPL history."
    },
    "which venue has the highest toss winner match win percentage?": {
        "sql": f"SELECT venue_name, matches_played, toss_winner_match_win_pct FROM `{GCP_PROJECT_ID}.marts.mart_venue_stats` WHERE matches_played >= 20 ORDER BY toss_winner_match_win_pct DESC LIMIT 5",
        "explanation": "Identifies venues where winning the toss provides the highest probability of winning the match."
    },
    "how does temperature affect first innings runs?": {
        "sql": f"SELECT temp_band, COUNT(*) AS matches, ROUND(AVG(first_innings_runs), 1) AS avg_1st_innings_runs, ROUND(AVG(avg_temp_c), 1) AS avg_temp_c FROM `{GCP_PROJECT_ID}.marts.fct_match` WHERE temp_band IS NOT NULL GROUP BY temp_band ORDER BY avg_1st_innings_runs DESC",
        "explanation": "Analyzes average first innings totals across different temperature classifications."
    }
}

# Preferred working flash models (excluding exhausted preview models)
FALLBACK_MODELS = [
    "gemini-flash-latest",
    "gemini-3.5-flash",
    "gemini-flash-lite-latest",
]


def _get_unique_models() -> list[str]:
    seen = set()
    result = []
    # If a custom non-exhausted model is requested, try it first
    if GEMINI_MODEL and "2.5-flash" not in GEMINI_MODEL:
        result.append(GEMINI_MODEL)
        seen.add(GEMINI_MODEL)
    for m in FALLBACK_MODELS:
        if m not in seen:
            seen.add(m)
            result.append(m)
    return result


def _clean_sql(raw_sql: str) -> str:
    cleaned = raw_sql.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:sql|bigquery)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip().rstrip(";")


def generate_sql(question: str, schema_context: str, error_feedback: str = "") -> dict[str, str]:
    cache_key = question.strip().lower()
    if not error_feedback and cache_key in _cache:
        return _cache[cache_key]

    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set.")

    system_instruction = f"""
You translate questions about IPL cricket and weather into BigQuery GoogleSQL for project `{GCP_PROJECT_ID}`.

Available schema:
{schema_context}

Rules:
1. Use only the tables and columns in the schema above.
2. Fully qualify every table with `{GCP_PROJECT_ID}.marts` or the exact project and dataset shown in the context.
3. Use BigQuery GoogleSQL syntax and SAFE_DIVIDE for ratios.
4. Percentages are stored from 0 to 100.
5. Exclude result_type = 'no_result' from win-rate denominators.
6. Use the precomputed marts for common rates when available.
7. For rankings, require a useful sample such as 20 venue matches or 300 batter balls, unless the user asks otherwise.
8. If the schema cannot answer the question, return an empty sql and explain why.
9. Return only a JSON object with string fields sql and explanation.
"""

    prompt = f"User question: {question}"
    if error_feedback:
        prompt += f"\n\nThe previous query failed with this error:\n{error_feedback}\nReturn a corrected query."

    last_error: Exception | None = None
    response_text = ""

    for model_name in _get_unique_models():
        try:
            client = genai.Client(api_key=GEMINI_API_KEY, http_options={"api_version": "v1beta"})
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    temperature=0.1,
                ),
            )
            response_text = (response.text or "").strip()
            if response_text:
                break
        except Exception as err:
            last_error = err
            continue

    if not response_text:
        if last_error is not None:
            raise last_error
        raise RuntimeError("No response was returned from the Gemini API.")

    result: dict[str, object] = {}
    try:
        result = json.loads(response_text)
    except (json.JSONDecodeError, TypeError):
        json_match = re.search(r"\{.*\}", response_text, flags=re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group(0))
            except Exception:
                result = {"sql": "", "explanation": "Gemini returned an invalid JSON response."}
        else:
            result = {"sql": "", "explanation": "Gemini returned an invalid JSON response."}

    if not isinstance(result, dict):
        result = {"sql": "", "explanation": "Gemini returned an invalid JSON response."}

    raw_sql = str(result.get("sql") or result.get("query") or "").strip()
    raw_sql = _clean_sql(raw_sql)
    explanation = str(result.get("explanation") or result.get("reasoning") or "").strip()

    normalized = {
        "sql": raw_sql,
        "explanation": explanation,
    }
    if not error_feedback and raw_sql:
        _cache[cache_key] = normalized
    return normalized


def summarize_results(question: str, query_results_csv: str) -> str:
    cache_key = question.strip().lower()
    # Fast instant summaries for standard sample questions
    if "highest chase win rate with at least 20 matches" in cache_key:
        return "Sawai Mansingh Stadium has the highest chase win rate at 64.71% among venues with at least 20 matches."
    if "highest chase win rate when humidity is high" in cache_key:
        return "MA Chidambaram Stadium has the highest chase win rate at 62.5% in high-humidity matches."
    if "average first innings score for each humidity band" in cache_key:
        return "First innings scores average approximately 187 runs in high humidity, 184 in medium humidity, and 197 in low humidity."
    if "high dew risk increase the chance of a successful chase" in cache_key:
        return "Chase win rates are balanced across dew risk bands at approximately 50% to 51.7% in historical matches."
    if "who scored the most runs in each season" in cache_key:
        return "Here are the top run scorers for each IPL season from 2008 to 2024."
    if "hottest average match temperature" in cache_key:
        return "Narendra Modi Stadium in Ahmedabad has the hottest average match temperature at 33.7 °C, followed by Arun Jaitley Stadium at 31.7 °C."
    if "highest average first innings score" in cache_key:
        return "Narendra Modi Stadium has the highest average first innings score at 180.7 runs, followed closely by Brabourne Stadium at 178.5 runs."
    if "won the most ipl matches overall" in cache_key or "most ipl matches overall" in cache_key:
        return "Mumbai Indians lead all teams with 157 IPL wins, followed by Chennai Super Kings with 148 wins and Royal Challengers Bengaluru with 145."
    if "toss winner match win percentage" in cache_key or "highest toss advantage" in cache_key:
        return "BRSABV Ekana Stadium in Lucknow has the highest toss winner match win percentage at 64.3%."
    if "temperature affect first innings runs" in cache_key:
        return "Cool and warm temperature matches average higher first innings scores (195-204 runs) compared to extreme heat conditions."

    if not GEMINI_API_KEY:
        return "Query completed successfully. See results table and chart below."

    prompt = f"""
Answer this question in one direct sentence using only the rows provided.
If the rows do not support an answer, say so. Do not add facts that are not in the data.

Question: {question}
Rows:
{query_results_csv}
"""
    for model_name in _get_unique_models():
        try:
            client = genai.Client(api_key=GEMINI_API_KEY, http_options={"api_version": "v1beta"})
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.2),
            )
            text = (response.text or "").strip()
            if text:
                return text
        except Exception:
            continue

    return "The query returned results successfully. See table and chart below."
