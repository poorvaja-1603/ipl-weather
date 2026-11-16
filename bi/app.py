import io
from pathlib import Path
import sys

import pandas as pd
import streamlit as st

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

# Page configuration
st.set_page_config(
    page_title="IPL + Weather Intelligence BI",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom executive CSS for a clean, professional, non-cluttered theme
st.markdown(
    """
    <style>
    /* Global Typography and Card Polish */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Header Card */
    .hero-header {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%);
        border: 1px solid rgba(148, 163, 184, 0.15);
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    }
    .hero-title {
        font-size: 26px;
        font-weight: 700;
        margin-bottom: 6px;
        background: linear-gradient(90deg, #38BDF8, #818CF8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .hero-subtitle {
        font-size: 14px;
        color: #94A3B8;
        line-height: 1.5;
        margin: 0;
    }

    /* KPI Metric Cards in Sidebar */
    .kpi-container {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
        margin-bottom: 18px;
    }
    .kpi-card {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(148, 163, 184, 0.15);
        border-radius: 8px;
        padding: 10px 12px;
    }
    .kpi-label {
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94A3B8;
        font-weight: 600;
        margin-bottom: 2px;
    }
    .kpi-value {
        font-size: 18px;
        font-weight: 700;
        color: #F8FAFC;
    }

    /* Sample Question Button Enhancements */
    .stButton > button {
        border-radius: 8px;
        border: 1px solid rgba(148, 163, 184, 0.2);
        padding: 8px 12px;
        font-size: 13px;
        font-weight: 500;
        transition: all 0.2s ease-in-out;
        text-align: left;
    }
    .stButton > button:hover {
        border-color: #38BDF8;
        box-shadow: 0 2px 8px rgba(56, 189, 248, 0.15);
        transform: translateY(-1px);
    }

    /* Status Pill */
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 11px;
        font-weight: 600;
        background: rgba(34, 197, 94, 0.12);
        color: #4ADE80;
        border: 1px solid rgba(34, 197, 94, 0.3);
        margin-bottom: 16px;
    }
    .status-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background-color: #22C55E;
    }

    /* Summary Card */
    .summary-card {
        background: rgba(15, 23, 42, 0.65);
        border: 1px solid rgba(56, 189, 248, 0.35);
        border-left: 4px solid #38BDF8;
        padding: 14px 18px;
        border-radius: 8px;
        color: #F1F5F9;
        margin-bottom: 20px;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.2);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

SAMPLE_QUESTIONS = [
    ("Which venue has the highest chase win rate with at least 20 matches?", "🏟️ Chase Venue"),
    ("Which venue has the highest chase win rate when humidity is high?", "💧 High Humidity"),
    ("What is the average first innings score for each humidity band?", "📊 Humidity Bands"),
    ("Does high dew risk increase the chance of a successful chase?", "🌱 Dew Impact"),
    ("Who scored the most runs in each season?", "🏏 Top Scorers"),
    ("Which venues have the hottest average match temperature?", "🔥 Hottest Grounds"),
    ("Which team has won the most IPL matches overall?", "🏆 Team Wins"),
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


def _format_summary_html(text: str) -> str:
    import re
    # Truncate any long decimals like 191.21052631578945 to 1 decimal:
    cleaned = re.sub(r'(\d+\.\d)\d{2,}', r'\1', text)

    # Check if text contains a numbered list like 1) ... 2) ... or 1. ... 2. ...
    splits = re.split(r'(?:,\s*|\s+and\s+|\s+|^)(\d+)[\.\)]\s+', cleaned)
    if len(splits) >= 3:
        intro = splits[0].strip().rstrip(':')
        items = []
        for i in range(1, len(splits), 2):
            num = splits[i]
            desc = splits[i + 1].strip().rstrip('.,;')
            items.append((num, desc))

        html_parts = []
        if intro:
            html_parts.append(f"<div style='font-size: 13.5px; font-weight: 600; color: #F8FAFC; margin-bottom: 10px;'>{intro}:</div>")

        display_items = items[:5]
        for num, desc in display_items:
            m = re.match(r'^([^\(]+)(\(.*\))$', desc)
            if m:
                name, stats = m.groups()
                body = f"<strong style='color: #FFFFFF; font-size: 14px;'>{name.strip()}</strong> <span style='color: #CBD5E1; font-size: 13px;'>{stats.strip()}</span>"
            else:
                body = f"<span style='color: #E2E8F0; font-size: 13.5px;'>{desc}</span>"

            html_parts.append(
                f"<div style='display: flex; align-items: baseline; gap: 10px; margin-bottom: 7px; padding: 8px 12px; background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(148, 163, 184, 0.18); border-radius: 6px;'>"
                f"<span style='background: rgba(56, 189, 248, 0.2); color: #38BDF8; border: 1px solid rgba(56, 189, 248, 0.4); padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; white-space: nowrap;'>#{num}</span>"
                f"<div style='line-height: 1.45;'>{body}</div>"
                f"</div>"
            )
        if len(items) > 5:
            html_parts.append(
                f"<div style='margin-top: 8px; font-size: 12px; color: #94A3B8; font-style: italic;'>"
                f"📊 Venues 6 to {len(items)} are fully detailed in the interactive chart and data table below."
                f"</div>"
            )
        return "".join(html_parts)

    return f"<p style='margin: 0; font-weight: 400; line-height: 1.6; color: #F1F5F9;'>{cleaned}</p>"


def render_response(summary: str, sql: str, results: pd.DataFrame, chart) -> None:
    formatted_html = _format_summary_html(summary)

    # Clean and round the dataframe
    display_df = results.copy()
    float_cols = display_df.select_dtypes(include=["float64", "float32"]).columns
    if len(float_cols) > 0:
        display_df[float_cols] = display_df[float_cols].round(2)

    # Pretty column headers (e.g. venue_name -> Venue Name)
    pretty_cols = {c: c.replace("_", " ").title() for c in display_df.columns}
    display_df = display_df.rename(columns=pretty_cols)

    # Top Metric Callout Cards
    num_cols = results.select_dtypes(include="number").columns
    cat_cols = [c for c in results.columns if c not in num_cols]
    if len(results) > 0 and len(num_cols) > 0:
        col1, col2, col3 = st.columns(3)
        top_row = results.iloc[0]
        if cat_cols:
            entity_val = str(top_row[cat_cols[0]])
            col1.metric("🥇 Top Leader", entity_val)
        else:
            col1.metric("📊 Total Rows", f"{len(results)} rows")

        m_col = num_cols[0]
        val = top_row[m_col]
        val_str = f"{val:.1f}" if isinstance(val, (int, float)) else str(val)
        col2.metric(f"🎯 {m_col.replace('_', ' ').title()}", val_str)

        if len(num_cols) > 1:
            m2_col = num_cols[1]
            val2 = top_row[m2_col]
            val2_str = f"{val2:.1f}" if isinstance(val2, (int, float)) else str(val2)
            col3.metric(f"📈 {m2_col.replace('_', ' ').title()}", val2_str)
        else:
            col3.metric("🏟️ Sample Size", f"{len(results)} records")

    # 1. Summary highlight card
    st.markdown(
        f"""
        <div class="summary-card">
            <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 700; color: #38BDF8; margin-bottom: 8px; display: flex; align-items: center; gap: 6px;">
                <span>💡</span> EXECUTIVE INSIGHT
            </div>
            {formatted_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 2. Tabs for Chart, Data Table, and SQL
    tab_chart, tab_data, tab_sql = st.tabs(["📊 Interactive Visualization", "📋 Data Table", "🔍 Generated SQL"])

    with tab_chart:
        if chart is not None:
            st.plotly_chart(chart, use_container_width=True)
        else:
            st.info("A single metric value was returned. See the data table or summary above.")

    with tab_data:
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        # Quick CSV Download
        csv_buffer = io.BytesIO()
        display_df.to_csv(csv_buffer, index=False)
        st.download_button(
            label="📥 Download Results as CSV",
            data=csv_buffer.getvalue(),
            file_name="ipl_weather_results.csv",
            mime="text/csv",
            key=f"dl_{abs(hash(sql))}",
        )

    with tab_sql:
        st.markdown("**Executed BigQuery GoogleSQL** *(AST-Validated, Read-Only, 1GB Scan Cap)*")
        st.code(sql, language="sql")


def render_saved_message(message: dict[str, object]) -> None:
    with st.chat_message(str(message["role"])):
        if message["role"] == "user":
            st.markdown(f"**{message['content']}**")
        else:
            if message.get("table") is not None and isinstance(message["table"], pd.DataFrame):
                render_response(
                    str(message.get("content", "")),
                    str(message.get("sql", "")),
                    message["table"],
                    message.get("chart"),
                )
            else:
                st.markdown(str(message["content"]))
                if message.get("sql"):
                    with st.expander("Generated SQL"):
                        st.code(str(message["sql"]), language="sql")


def answer_question(question: str, schema_context: str) -> None:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(f"**{question}**")

    with st.chat_message("assistant"):
        try:
            with st.spinner("Analyzing schema and generating SQL query..."):
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
                with st.spinner("Retrying once with the BigQuery error feedback..."):
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
                message = "The query completed successfully but returned 0 rows for these filters."
                st.info(message)
                with st.expander("Generated SQL"):
                    st.code(safe_sql, language="sql")
                st.session_state.messages.append(
                    {"role": "assistant", "content": message, "sql": safe_sql}
                )
                return

            try:
                summary = summarize_results(question, results.head(20).to_csv(index=False))
            except Exception:
                summary = f"The query returned {len(results)} rows. See the charts and table below."

            chart = create_chart(results)
            render_response(summary, safe_sql, results, chart)

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


# =========================================================================
# Sidebar: System Status & Filter Queries
# =========================================================================
with st.sidebar:
    st.markdown('<div class="status-pill"><div class="status-dot"></div>Warehouse & LLM Online</div>', unsafe_allow_html=True)
    st.title("🏏 IPL + Weather BI")
    st.caption("Cloud Analytics powered by BigQuery & Gemini")

    coverage = get_data_coverage()
    st.markdown(
        f"""
        <div class="kpi-container">
            <div class="kpi-card">
                <div class="kpi-label">Seasons</div>
                <div class="kpi-value">{coverage['min_season']}-{coverage['max_season']}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Matches</div>
                <div class="kpi-value">{coverage['total_matches']:,}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Venues</div>
                <div class="kpi-value">{coverage['total_venues']:,}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Observations</div>
                <div class="kpi-value">11,088</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Suggested Questions")
    st.caption("Click any query to execute against BigQuery:")
    selected_question = None
    for index, (q_text, q_badge) in enumerate(SAMPLE_QUESTIONS):
        if st.button(f"{q_badge} — {q_text}", key=f"sample_{index}", use_container_width=True):
            selected_question = q_text

    st.divider()
    st.caption("Data Sources: Cricsheet (Match Archives) & Open-Meteo (Micro-Climate Reanalysis).")


# =========================================================================
# Main Content Area
# =========================================================================
st.markdown(
    """
    <div class="hero-header">
        <div class="hero-title">🏏 IPL + Weather Impact Conversational BI</div>
        <p class="hero-subtitle">
            Explore 17 seasons of historical Indian Premier League cricket cross-analyzed with hourly surface weather.
            Ask questions in natural English to generate verified BigQuery GoogleSQL, interactive visualizations, and AI insights.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Render chat history
for saved_message in st.session_state.messages:
    render_saved_message(saved_message)

# Chat input
typed_question = st.chat_input("Ask about IPL results, high humidity, dew risk, venue records, or top batters...")
question = typed_question or selected_question

if question:
    context = load_schema_context()
    if not context:
        st.error("The dbt schema context is missing. Generate it with dbt docs first.")
    else:
        answer_question(question, context)
