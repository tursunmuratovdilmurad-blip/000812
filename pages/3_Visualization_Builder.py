"""Visualization builder page."""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from utils.plotting import create_chart, filter_dataframe
from utils.session import get_current_df, has_dataset, init_session_state
from utils.ui import apply_shared_styles, render_page_header, render_section_header


init_session_state()
apply_shared_styles()

render_page_header(
    "Visualization Builder",
    "Filter the working dataset, choose a chart type, and build readable matplotlib visuals from the current data.",
    eyebrow="Charts & Exploration",
)

if not has_dataset():
    st.info("Load a dataset first, then come back here to build visualizations.")
    st.stop()

current_df = get_current_df()
numeric_columns = current_df.select_dtypes(include=[np.number]).columns.tolist()
categorical_columns = current_df.select_dtypes(include=["object", "category", "string"]).columns.tolist()

metric_col_1, metric_col_2, metric_col_3 = st.columns(3)
metric_col_1.metric("Rows", f"{len(current_df):,}")
metric_col_2.metric("Columns", current_df.shape[1])
metric_col_3.metric("Numeric Columns", len(numeric_columns))

render_section_header("Filters", "Limit the working dataset before building a chart.")
selected_category_filter_columns = st.multiselect("Category filter columns", categorical_columns)
selected_numeric_filter_columns = st.multiselect("Numeric range filter columns", numeric_columns)

category_filters: dict[str, list[object]] = {}
for column in selected_category_filter_columns:
    options = current_df[column].dropna().astype(str).unique().tolist()
    options = sorted(options)[:250]
    selected_values = st.multiselect(f"Allowed values for {column}", options=options, default=options)
    if selected_values and len(selected_values) != len(options):
        category_filters[column] = selected_values

numeric_filters: dict[str, tuple[float, float]] = {}
for column in selected_numeric_filter_columns:
    series = pd.to_numeric(current_df[column], errors="coerce").dropna()
    if series.empty:
        st.warning(f"Column '{column}' does not contain usable numeric values for range filtering.")
        continue
    min_value = float(series.min())
    max_value = float(series.max())
    if min_value == max_value:
        st.info(f"Column '{column}' has a constant value of {min_value}, so no range filter is needed.")
        continue
    selected_range = st.slider(
        f"Range for {column}",
        min_value=min_value,
        max_value=max_value,
        value=(min_value, max_value),
    )
    if selected_range != (min_value, max_value):
        numeric_filters[column] = selected_range

filtered_df = filter_dataframe(current_df, categorical_filters=category_filters, numeric_filters=numeric_filters)

filtered_metric_col_1, filtered_metric_col_2 = st.columns(2)
filtered_metric_col_1.metric("Rows After Filtering", f"{len(filtered_df):,}")
filtered_metric_col_2.metric("Columns After Filtering", filtered_df.shape[1])

with st.expander("Filtered Data Preview", expanded=False):
    st.dataframe(filtered_df.head(20), width="stretch")

chart_label_to_key = {
    "Histogram": "histogram",
    "Box Plot": "box",
    "Scatter Plot": "scatter",
    "Line Chart": "line",
    "Bar Chart": "bar",
    "Heatmap / Correlation Matrix": "heatmap",
}

render_section_header("Chart Builder", "Choose the chart structure and the columns to plot.")
selected_chart_label = st.selectbox("Chart type", list(chart_label_to_key))
chart_type = chart_label_to_key[selected_chart_label]

x_column = None
y_column = None
group_column = None
aggregation = None
heatmap_columns = None
top_n = None
bins = 20

all_columns = filtered_df.columns.tolist()
all_numeric_columns = filtered_df.select_dtypes(include=[np.number]).columns.tolist()

optional_columns = [None] + all_columns
optional_numeric_columns = [None] + all_numeric_columns

if chart_type == "histogram":
    x_column = st.selectbox("X column (numeric)", all_numeric_columns if all_numeric_columns else [""])
    group_column = st.selectbox("Group / color column (optional)", optional_columns, format_func=lambda value: value or "None")
    bins = st.slider("Number of bins", min_value=5, max_value=60, value=20)

elif chart_type == "box":
    x_column = st.selectbox("X column (optional group axis)", optional_columns, format_func=lambda value: value or "None")
    y_column = st.selectbox("Y column (numeric)", all_numeric_columns if all_numeric_columns else [""])
    group_column = st.selectbox("Alternate group column (optional)", optional_columns, format_func=lambda value: value or "None")

elif chart_type == "scatter":
    x_column = st.selectbox("X column (numeric)", all_numeric_columns if all_numeric_columns else [""])
    y_column = st.selectbox("Y column (numeric)", all_numeric_columns if all_numeric_columns else [""])
    group_column = st.selectbox("Group / color column (optional)", optional_columns, format_func=lambda value: value or "None")

elif chart_type == "line":
    x_column = st.selectbox("X column", all_columns if all_columns else [""])
    y_column = st.selectbox("Y column (numeric)", all_numeric_columns if all_numeric_columns else [""])
    group_column = st.selectbox("Group / color column (optional)", optional_columns, format_func=lambda value: value or "None")
    aggregation = st.selectbox(
        "Aggregation (optional)",
        [None, "sum", "mean", "count", "median"],
        format_func=lambda value: value.title() if value else "None",
    )

elif chart_type == "bar":
    x_column = st.selectbox("X column", all_columns if all_columns else [""])
    y_column = st.selectbox(
        "Y column (optional for count charts)",
        optional_numeric_columns,
        format_func=lambda value: value or "None",
    )
    group_column = st.selectbox("Group / color column (optional)", optional_columns, format_func=lambda value: value or "None")
    aggregation = st.selectbox(
        "Aggregation",
        [None, "sum", "mean", "count", "median"],
        format_func=lambda value: value.title() if value else "None",
    )
    top_n = st.number_input("Top N categories (optional, 0 = all)", min_value=0, max_value=50, value=10, step=1)

else:
    default_heatmap_columns = all_numeric_columns[: min(8, len(all_numeric_columns))]
    heatmap_columns = st.multiselect(
        "Numeric columns for the correlation matrix",
        all_numeric_columns,
        default=default_heatmap_columns,
    )

render_section_header("Formatting", "Adjust titles, labels, and figure size for a clearer final chart.")
format_col_1, format_col_2, format_col_3 = st.columns(3)
with format_col_1:
    chart_title = st.text_input("Chart title", value=selected_chart_label)
    x_label = st.text_input("X-axis label", value="")
with format_col_2:
    y_label = st.text_input("Y-axis label", value="")
    x_rotation = st.slider("X label rotation", min_value=0, max_value=90, value=30)
with format_col_3:
    figure_width = st.slider("Figure width", min_value=6, max_value=18, value=10)
    figure_height = st.slider("Figure height", min_value=4, max_value=12, value=6)

if st.button("Generate chart", type="primary"):
    try:
        figure = create_chart(
            filtered_df,
            chart_type=chart_type,
            x_column=x_column,
            y_column=y_column,
            group_column=group_column,
            aggregation=aggregation,
            title=chart_title,
            x_label=x_label or None,
            y_label=y_label or None,
            rotation=x_rotation,
            figsize=(float(figure_width), float(figure_height)),
            bins=bins,
            top_n=int(top_n) if top_n and top_n > 0 else None,
            heatmap_columns=heatmap_columns,
        )
        st.pyplot(figure, clear_figure=True)
    except ValueError as exc:
        st.error(str(exc))
