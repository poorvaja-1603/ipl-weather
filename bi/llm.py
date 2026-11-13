import json
from google import genai
from google.genai import types
from bi.config import GEMINI_API_KEY, GEMINI_MODEL

_cache: dict[str, dict] = {}

def get_gemini_client() -> genai.Client:
    return genai.Client(api_key=GEMINI_API_KEY)

def generate_sql(question: str, schema_context: str, error_feedback: str = "") -> dict:
    cache_key = question.strip().lower()
    if not error_feedback and cache_key in _cache:
        return _cache[cache_key]

    system_instruction = f"""
You are an expert Snowflake SQL data analyst for an IPL and Weather data warehouse.
Your role is to translate English user questions into Snowflake SQL queries.

Database context:
{schema_context}

Rules:
1. Snowflake SQL dialect only.
2. Use only tables listed in the schema context, and always use fully qualified names: IPL_DB.MARTS.<TABLE_NAME>.
3. Percentages are stored as 0 to 100 values (e.g., 55.4 for 55.4%).
4. Always exclude 'no_result' matches when computing win rates (prefer precomputed marts when available).
5. When ranking or finding best/worst records, add a sample size filter (e.g. at least 20 matches for venues, at least 300 balls for batters) unless specified otherwise.
6. Never invent columns or tables.
7. Return your response ONLY as valid JSON with two fields:
   "sql": "<Snowflake SQL query string or empty string if question cannot be answered>",
   "explanation": "<Brief explanation of what the query calculates or reason if unable to answer>"
"""

    prompt = f"User Question: {question}"
    if error_feedback:
        prompt += f"\n\nPrevious SQL attempt failed with error:\n{error_feedback}\nPlease correct the query."

    client = get_gemini_client()
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            temperature=0.1
        )
    )

    try:
        res = json.loads(response.text)
    except Exception:
        res = {"sql": "", "explanation": response.text}

    if not error_feedback:
        _cache[cache_key] = res

    return res

def summarize_results(question: str, query_results_csv: str) -> str:
    prompt = f"""
Given the user question: "{question}"
And the top query results (in CSV format):
{query_results_csv}

Provide a direct, factual answer in 1 or 2 plain English sentences. Do not use markdown headers, bullets, or em dashes.
"""
    client = get_gemini_client()
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.2
        )
    )
    return response.text.strip()
