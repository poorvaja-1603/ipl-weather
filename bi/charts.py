import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def create_chart(df: pd.DataFrame) -> go.Figure | None:
    if df.empty or len(df.columns) < 2:
        return None

    columns = df.columns.tolist()
    numeric_columns = df.select_dtypes(include="number").columns.tolist()
    categorical_columns = [column for column in columns if column not in numeric_columns]
    if not numeric_columns:
        return None

    time_columns = [
        column
        for column in columns
        if any(key in column.lower() for key in ("date", "year", "season", "observed_at"))
    ]
    for x_column in time_columns:
        y_candidates = [column for column in numeric_columns if column != x_column]
        if y_candidates:
            sorted_df = df.sort_values(by=x_column)
            figure = px.line(
                sorted_df,
                x=x_column,
                y=y_candidates[0],
                title=f"{y_candidates[0].replace('_', ' ').title()} by {x_column.replace('_', ' ').title()}",
                markers=True,
            )
            figure.update_layout(template="plotly_white")
            return figure

    if categorical_columns:
        x_column = categorical_columns[0]
        y_column = numeric_columns[0]
        figure = px.bar(
            df.head(15),
            x=x_column,
            y=y_column,
            title=f"{y_column.replace('_', ' ').title()} by {x_column.replace('_', ' ').title()}",
        )
        figure.update_layout(template="plotly_white")
        return figure

    return None
