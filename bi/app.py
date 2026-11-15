import sys
from pathlib import Path
import streamlit as st
import pandas as pd

# Add project root and bi directory to sys.path for Streamlit Cloud compatibility
root_dir = Path(__file__).resolve().parent.parent
bi_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
if str(bi_dir) not in sys.path:
    sys.path.insert(0, str(bi_dir))

try:
    from bi.db import run_query
    from bi.sql_guard import validate_and_guard_sql
    from bi.llm import generate_sql, summarize_results
    from bi.charts import create_chart
except ImportError:
    from db import run_query
    from sql_guard import validate_and_guard_sql
    from llm import generate_sql, summarize_results
    from charts import create_chart

st.set_page_config(page_title="IPL + Weather Impact BI", layout="wide")

@st.cache_data(ttl=600)
def load_schema_context() -> str:
    ctx_path = Path("bi/context/schema_context.md")
    if ctx_path.exists():
        return ctx_path.read_text(encoding="utf-8")
    return "Schema context not available."

@st.cache_data(ttl=600)
def get_data_coverage() -> dict:
    try:
        sql = """
            SELECT 
                MIN(season_year) as min_season,
                MAX(season_year) as max_season,
                COUNT(DISTINCT match_id) as total_matches,
                COUNT(DISTINCT venue_id) as total_venues
            FROM IPL_DB.MARTS.FCT_MATCH
        """
        df = run_query(sql)
        if not df.empty:
            return df.iloc[0].to_dict()
    except Exception:
        pass
    return {"min_season": 2008, "max_season": 2024, "total_matches": 1000, "total_venues": 35}

# Sidebar
st.sidebar.title("IPL + Weather BI")
coverage = get_data_coverage()
st.sidebar.markdown(f"**Coverage:** {coverage.get('min_season')} - {coverage.get('max_season')}")
st.sidebar.markdown(f"**Total Matches:** {coverage.get('total_matches')}")
st.sidebar.markdown(f"**Total Venues:** {coverage.get('total_venues')}")

st.sidebar.markdown("---")
st.sidebar.subheader("Sample Questions")
sample_questions = [
    "Which venue has the highest chase win rate with at least 20 matches?",
    "Which venue has the highest chase win rate when humidity is high?",
    "What is the average first innings score for each humidity band?",
    "Does high dew risk increase the chance of a successful chase?",
    "Who scored the most runs in each season?"
]

if "messages" not in st.session_state:
    st.session_state.messages = []

for q in sample_questions:
    if st.sidebar.button(q, key=f"btn_{q}"):
        st.session_state.messages.append({"role": "user", "content": q})

st.title("IPL + Weather Impact Conversational BI")
st.caption("Ask questions about IPL match statistics and ambient weather conditions.")

schema_ctx = load_schema_context()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "sql" in msg:
            with st.expander("Generated SQL"):
                st.code(msg["sql"], language="sql")
        if "table" in msg and msg["table"] is not None:
            st.dataframe(msg["table"])
        if "chart" in msg and msg["chart"] is not None:
            st.plotly_chart(msg["chart"], use_container_width=True)

user_input = st.chat_input("Ask a question about IPL stats and weather...")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Generating query with Gemini..."):
            llm_result = generate_sql(user_input, schema_ctx)
            raw_sql = llm_result.get("sql", "").strip()

            if not raw_sql:
                explanation = llm_result.get("explanation", "I cannot answer this question with the available marts.")
                st.markdown(explanation)
                st.session_state.messages.append({"role": "assistant", "content": explanation})
            else:
                is_safe, safe_sql, guard_err = validate_and_guard_sql(raw_sql)
                if not is_safe:
                    err_msg = f"SQL Guard rejected query: {guard_err}"
                    st.error(err_msg)
                    st.session_state.messages.append({"role": "assistant", "content": err_msg, "sql": raw_sql})
                else:
                    try:
                        df = run_query(safe_sql)
                    except Exception as first_err:
                        llm_retry = generate_sql(user_input, schema_ctx, error_feedback=str(first_err))
                        retry_raw_sql = llm_retry.get("sql", "").strip()
                        is_safe, safe_sql, guard_err = validate_and_guard_sql(retry_raw_sql)
                        if is_safe:
                            df = run_query(safe_sql)
                        else:
                            df = pd.DataFrame()

                    if df.empty:
                        reply = "Query returned no results."
                        st.markdown(reply)
                        st.session_state.messages.append({"role": "assistant", "content": reply, "sql": safe_sql})
                    else:
                        csv_sample = df.head(20).to_csv(index=False)
                        summary = summarize_results(user_input, csv_sample)
                        st.markdown(summary)
                        with st.expander("Generated SQL"):
                            st.code(safe_sql, language="sql")
                        st.dataframe(df)

                        fig = create_chart(df)
                        if fig:
                            st.plotly_chart(fig, use_container_width=True)

                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": summary,
                            "sql": safe_sql,
                            "table": df,
                            "chart": fig
                        })
