import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def _choose_color_scale(metric_name: str) -> str:
    name = metric_name.lower()
    if any(k in name for k in ("temp", "heat", "hot", "warm")):
        return "Sunsetdark"
    if any(k in name for k in ("humidity", "dew", "precip", "rain", "wind", "weather")):
        return "Tealgrn"
    if any(k in name for k in ("win", "rate", "pct", "percent")):
        return "Viridis"
    if any(k in name for k in ("runs", "score", "fours", "sixes", "strike")):
        return "Plasma"
    if any(k in name for k in ("wicket", "balls", "economy", "bowler")):
        return "Spectral"
    return "Turbo"


def create_chart(df: pd.DataFrame) -> go.Figure | None:
    if df.empty or len(df.columns) < 2:
        return None

    columns = df.columns.tolist()
    numeric_columns = df.select_dtypes(include="number").columns.tolist()
    categorical_columns = [col for col in columns if col not in numeric_columns]

    if not numeric_columns:
        return None

    # Base layout styling for modern, non-cluttered aesthetics
    layout_theme = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif", size=12),
        margin=dict(l=40, r=40, t=50, b=50),
        hoverlabel=dict(
            bgcolor="rgba(25, 30, 45, 0.95)",
            font_size=12,
            font_family="Inter, sans-serif",
            bordercolor="rgba(255, 255, 255, 0.2)",
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor="rgba(128, 128, 128, 0.15)",
            gridwidth=1,
            linecolor="rgba(128, 128, 128, 0.3)",
            tickfont=dict(size=11),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(128, 128, 128, 0.15)",
            gridwidth=1,
            linecolor="rgba(128, 128, 128, 0.3)",
            tickfont=dict(size=11),
        ),
    )

    # 1. Time-series / Trend Line Chart (Season, Year, Date)
    time_columns = [
        col
        for col in columns
        if any(key in col.lower() for key in ("date", "year", "season", "observed_at"))
    ]
    if time_columns:
        x_col = time_columns[0]
        y_candidates = [col for col in numeric_columns if col != x_col]
        if y_candidates:
            y_col = y_candidates[0]
            sorted_df = df.sort_values(by=x_col)
            palette = _choose_color_scale(y_col)

            figure = px.line(
                sorted_df,
                x=x_col,
                y=y_col,
                title=f"<b>{y_col.replace('_', ' ').title()}</b> across {x_col.replace('_', ' ').title()}",
                markers=True,
            )
            figure.update_traces(
                line=dict(width=3, shape="spline"),
                marker=dict(size=8, symbol="circle", line=dict(width=1.5, color="#ffffff")),
                fill="tozeroy",
                fillcolor="rgba(56, 178, 172, 0.12)",
                hovertemplate=f"<b>%{{x}}</b><br>{y_col.replace('_', ' ').title()}: <b>%{{y:.2f}}</b><extra></extra>",
            )
            figure.update_layout(**layout_theme)
            return figure

    # 2. Scatter Plot if 2 continuous numeric variables + 1 categorical label
    if len(numeric_columns) >= 2 and categorical_columns and len(df) >= 4:
        x_col = numeric_columns[0]
        y_col = numeric_columns[1]
        label_col = categorical_columns[0]
        color_col = numeric_columns[2] if len(numeric_columns) >= 3 else y_col
        palette = _choose_color_scale(y_col)

        # Only use scatter if both numeric columns have varied values and aren't row counts
        if df[x_col].nunique() > 3 and df[y_col].nunique() > 3:
            figure = px.scatter(
                df.head(25),
                x=x_col,
                y=y_col,
                color=color_col,
                text=label_col,
                color_continuous_scale=palette,
                title=f"<b>{y_col.replace('_', ' ').title()}</b> vs <b>{x_col.replace('_', ' ').title()}</b>",
            )
            figure.update_traces(
                textposition="top center",
                marker=dict(size=12, opacity=0.88, line=dict(width=1, color="rgba(255,255,255,0.6)")),
                hovertemplate=f"<b>%{{text}}</b><br>{x_col.replace('_', ' ').title()}: %{{x}}<br>{y_col.replace('_', ' ').title()}: %{{y}}<extra></extra>",
            )
            figure.update_layout(**layout_theme)
            return figure

    # 3. Bar Chart for Categorical Rankings (Venues, Teams, Players, Weather Bands)
    if categorical_columns:
        x_col = categorical_columns[0]
        y_col = numeric_columns[0]
        plot_df = df.head(12).copy()
        palette = _choose_color_scale(y_col)

        # If categories have long names (like full stadium names), use horizontal bars for crisp readability
        max_str_len = plot_df[x_col].astype(str).str.len().max()
        use_horizontal = max_str_len > 15 and len(plot_df) >= 3

        if use_horizontal:
            plot_df = plot_df.sort_values(by=y_col, ascending=True)
            figure = px.bar(
                plot_df,
                x=y_col,
                y=x_col,
                orientation="h",
                color=y_col,
                color_continuous_scale=palette,
                text=y_col,
                title=f"<b>{y_col.replace('_', ' ').title()}</b> by {x_col.replace('_', ' ').title()}",
            )
            figure.update_traces(
                texttemplate="%{x:.1f}" if plot_df[y_col].dtype == "float64" else "%{x}",
                textposition="inside",
                insidetextanchor="end",
                marker=dict(line=dict(width=0.8, color="rgba(255, 255, 255, 0.4)")),
                hovertemplate=f"<b>%{{y}}</b><br>{y_col.replace('_', ' ').title()}: <b>%{{x}}</b><extra></extra>",
            )
        else:
            plot_df = plot_df.sort_values(by=y_col, ascending=False)
            figure = px.bar(
                plot_df,
                x=x_col,
                y=y_col,
                color=y_col,
                color_continuous_scale=palette,
                text=y_col,
                title=f"<b>{y_col.replace('_', ' ').title()}</b> by {x_col.replace('_', ' ').title()}",
            )
            figure.update_traces(
                texttemplate="%{y:.1f}" if plot_df[y_col].dtype == "float64" else "%{y}",
                textposition="outside",
                marker=dict(line=dict(width=0.8, color="rgba(255, 255, 255, 0.4)")),
                hovertemplate=f"<b>%{{x}}</b><br>{y_col.replace('_', ' ').title()}: <b>%{{y}}</b><extra></extra>",
            )

        figure.update_coloraxes(showscale=False)
        figure.update_layout(**layout_theme)
        return figure

    return None
