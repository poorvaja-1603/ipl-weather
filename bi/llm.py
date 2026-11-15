import json
import re

from google import genai
from google.genai import types

from bi.config import GEMINI_API_KEY, GEMINI_MODEL, GCP_PROJECT_ID


_cache: dict[str, dict[str, str]] = {}
_client: genai.Client | None = None


def get_gemini_client() -> genai.Client:
    global _client
    if _client is None:
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set.")
        _client = genai.Client(api_key=GEMINI_API_KEY, http_options={"api_version": "v1beta"})
    return _client


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

    client = get_gemini_client()
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            temperature=0.1,
        ),
    )

    text = (response.text or "").strip()
    result: dict[str, object] = {}
    try:
        result = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        # Fallback: regex search for JSON inside potential markdown
        json_match = re.search(r"\{.*\}", text, flags=re.DOTALL)
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
    prompt = f"""
Answer this question in one or two direct sentences using only the rows provided.
If the rows do not support an answer, say so. Do not add facts that are not in the data.

Question: {question}
Rows:
{query_results_csv}
"""
    client = get_gemini_client()
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.2),
    )
    return (response.text or "No summary was returned.").strip()
