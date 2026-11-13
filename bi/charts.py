import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def create_chart(df: pd.DataFrame) -> go.Figure | None:
    if df.empty or len(df.columns) < 2:
        return None

    cols = df.columns.tolist()
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    non_numeric_cols = [c for c in cols if c not in numeric_cols]

    if not numeric_cols:
        return None

    # Check for date or year columns for line chart
    date_cols = [c for c in cols if any(k in c.lower() for k in ['date', 'year', 'season', 'observed_at'])]
    if date_cols and numeric_cols:
        x_col = date_cols[0]
        y_col = [c for c in numeric_cols if c != x_col][0] if len(numeric_cols) > 1 or numeric_cols[0] != x_col else numeric_cols[0]
        sorted_df = df.sort_values(by=x_col)
        fig = px.line(sorted_df, x=x_col, y=y_col, title=f"{y_col.replace('_', ' ').title()} over {x_col.replace('_', ' ').title()}", markers=True)
        fig.update_layout(template="plotly_white")
        return fig

    # Check for categorical + numeric for bar chart
    if non_numeric_cols and numeric_cols:
        x_col = non_numeric_cols[0]
        y_col = numeric_cols[0]
        top_df = df.head(15)
        fig = px.bar(top_df, x=x_col, y=y_col, title=f"{y_col.replace('_', ' ').title()} by {x_col.replace('_', ' ').title()}")
        fig.update_layout(template="plotly_white")
        return fig

    return None
