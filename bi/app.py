from pathlib import Path

import pandas as pd
import streamlit as st

import sys

# Keep imports working in both repository-root and Streamlit Cloud launches.
root_dir = Path(__file__).resolve().parent.parent
bi_dir = Path(__file__).resolve().parent
for import_dir in (str(root_dir), str(bi_dir)):
    if import_dir not in sys.path:
        sys.path.insert(0, import_dir)

from bi.charts import create_chart
from bi.config import GCP_PROJECT_ID
from bi.db import run_query
from bi.llm import generate_sql, summarize_results
from bi.sql_guard import validate_and_guard_sql


st.set_page_config(page_title="IPL + Weather Impact BI", layout="wide")

SAMPLE_QUESTIONS = [
    "Which venue has the highest chase win rate with at least 20 matches?",
    "Which venue has the highest chase win rate when humidity is high?",
    "What is the average first innings score for each humidity band?",
    "Does high dew risk increase the chance of a successful chase?",
    "Who scored the most runs in each season?",
]


@st.cache_data(ttl=600)
def load_schema_context() -> str:
    context_path = Path(__file__).resolve().parent / "context" / "schema_context.md"
    if context_path.is_file():
        return context_path.read_text(encoding="utf-8")
    return ""


@st.cache_data(ttl=600)
def get_data_coverage() -> dict[str, object]:
    try:
        sql = f"""
            SELECT MIN(season_year) AS min_season,
                MAX(season_year) AS max_season,
                COUNT(DISTINCT match_id) AS total_matches,
                COUNT(DISTINCT venue_id) AS total_venues
            FROM `{GCP_PROJECT_ID}.marts.fct_match`
        """
        df = run_query(sql)
        if not df.empty:
            return df.iloc[0].to_dict()
    except Exception:
        pass
    return {"min_season": 2008, "max_season": 2024, "total_matches": 1243, "total_venues": 36}


def render_saved_message(message: dict[str, object]) -> None:
    with st.chat_message(str(message["role"])):
        st.markdown(str(message["content"]))
        if message.get("sql"):
            with st.expander("Generated SQL"):
                st.code(str(message["sql"]), language="sql")
        if isinstance(message.get("table"), pd.DataFrame):
            st.dataframe(message["table"], use_container_width=True)
        if message.get("chart") is not None:
            st.plotly_chart(message["chart"], use_container_width=True)


def answer_question(question: str, schema_context: str) -> None:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Generating a BigQuery query..."):
                generated = generate_sql(question, schema_context)
            raw_sql = generated.get("sql", "").strip()
            if not raw_sql:
                explanation = generated.get("explanation") or "I cannot answer that from the available marts."
                st.markdown(explanation)
                st.session_state.messages.append({"role": "assistant", "content": explanation})
                return

            is_safe, safe_sql, guard_error = validate_and_guard_sql(raw_sql)
            if not is_safe:
                message = f"The SQL guard rejected the query: {guard_error}"
                st.error(message)
                st.session_state.messages.append(
                    {"role": "assistant", "content": message, "sql": raw_sql}
                )
                return

            try:
                results = run_query(safe_sql)
            except Exception as first_error:
                with st.spinner("Retrying once with the BigQuery error..."):
                    retry = generate_sql(question, schema_context, error_feedback=str(first_error))
                retry_sql = retry.get("sql", "").strip()
                is_safe, retry_safe_sql, guard_error = validate_and_guard_sql(retry_sql)
                if not is_safe:
                    message = f"The retry was rejected by the SQL guard: {guard_error}"
                    st.error(message)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": message, "sql": raw_sql}
                    )
                    return
                safe_sql = retry_safe_sql
                results = run_query(safe_sql)

            if results.empty:
                message = "The query returned no rows."
                st.markdown(message)
                with st.expander("Generated SQL"):
                    st.code(safe_sql, language="sql")
                st.session_state.messages.append(
                    {"role": "assistant", "content": message, "sql": safe_sql}
                )
                return

            try:
                summary = summarize_results(question, results.head(20).to_csv(index=False))
            except Exception:
                summary = f"The query returned {len(results)} rows. See the results below."

            st.markdown(summary)
            with st.expander("Generated SQL"):
                st.code(safe_sql, language="sql")
            st.dataframe(results, use_container_width=True)
            chart = create_chart(results)
            if chart is not None:
                st.plotly_chart(chart, use_container_width=True)
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": summary,
                    "sql": safe_sql,
                    "table": results,
                    "chart": chart,
                }
            )
        except Exception as error:
            message = f"The request failed: {error}"
            st.error(message)
            st.session_state.messages.append({"role": "assistant", "content": message})


st.title("IPL + Weather Impact Conversational BI")
st.caption("Ask questions about IPL match statistics and historical weather.")

with st.sidebar:
    st.title("IPL + Weather BI")
    try:
        coverage = get_data_coverage()
        st.markdown(f"**Seasons:** {coverage['min_season']} to {coverage['max_season']}")
        st.markdown(f"**Matches:** {coverage['total_matches']:,}")
        st.markdown(f"**Venues:** {coverage['total_venues']:,}")
    except Exception:
        st.info("Data coverage will appear after the marts are built.")

    st.divider()
    st.subheader("Sample questions")
    selected_question = None
    for index, question in enumerate(SAMPLE_QUESTIONS):
        if st.button(question, key=f"sample_{index}", use_container_width=True):
            selected_question = question

if "messages" not in st.session_state:
    st.session_state.messages = []

for saved_message in st.session_state.messages:
    render_saved_message(saved_message)

typed_question = st.chat_input("Ask about IPL results or weather...")
question = typed_question or selected_question
if question:
    context = load_schema_context()
    if not context:
        st.error("The dbt schema context is missing. Generate it with dbt docs first.")
    else:
        answer_question(question, context)

st.divider()
st.caption("Match data from Cricsheet (cricsheet.org). Weather data from Open-Meteo.com.")
