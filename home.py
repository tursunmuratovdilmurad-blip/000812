"""Home page for the coursework project."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.session import get_current_df, get_transformation_log, has_dataset, init_session_state
from utils.ui import apply_shared_styles


init_session_state()
apply_shared_styles()

st.title("AI-Assisted Data Wrangler & Visualizer")
st.caption("A compact analytics workspace for loading data, cleaning common issues, building charts, and exporting a clear final result.")
st.markdown(
    "This project brings the full coursework workflow into one place: upload a dataset, inspect it, clean it step by step, "
    "build charts, and export both the final data and a simple record of the work completed."
)

hero_metrics = st.columns(4)
hero_metrics[0].metric("File Inputs", "CSV / XLSX / JSON")
hero_metrics[1].metric("Cleaning Tools", "8+ sections")
hero_metrics[2].metric("Chart Types", "6")
hero_metrics[3].metric("Exports", "CSV / XLSX / JSON / MD")

st.subheader("What You Can Do Here")
st.caption("The app keeps the coursework workflow simple and practical from start to finish.")

feature_row_1 = st.columns(2)
with feature_row_1[0]:
    with st.container(border=True):
        st.markdown("#### Upload and Profile")
        st.caption("Start with your own dataset or one of the bundled samples, then review shape, data types, missing values, and duplicates.")
with feature_row_1[1]:
    with st.container(border=True):
        st.markdown("#### Clean with Control")
        st.caption("Handle nulls, duplicates, type conversion, category cleanup, scaling, formulas, and validation without leaving the workflow.")

feature_row_2 = st.columns(2)
with feature_row_2[0]:
    with st.container(border=True):
        st.markdown("#### Build Clear Charts")
        st.caption("Filter the working dataset and create histograms, scatter plots, box plots, line charts, bar charts, and heatmaps.")
with feature_row_2[1]:
    with st.container(border=True):
        st.markdown("#### Export the Result")
        st.caption("Download the cleaned dataset, a transformation recipe, and a readable summary file for coursework evidence.")

st.subheader("Workflow")
st.caption("Move through the project in a clear order from data intake to export.")

workflow_cols = st.columns(4)
workflow_steps = [
    ("Step 1", "Load a Dataset", "Upload a CSV, XLSX, or JSON file, or use one of the bundled sample datasets."),
    ("Step 2", "Prepare the Data", "Apply cleaning steps carefully and use undo or reset if you need to roll back changes."),
    ("Step 3", "Explore Visually", "Generate charts from the current working dataset to inspect patterns and outliers."),
    ("Step 4", "Export Outputs", "Download the cleaned dataset together with the transformation report and summary."),
]

for column, (step_label, title, body) in zip(workflow_cols, workflow_steps):
    with column:
        with st.container(border=True):
            st.caption(step_label)
            st.markdown(f"#### {title}")
            st.caption(body)

if has_dataset():
    current_df = get_current_df()
    log_entries = get_transformation_log()
    dataset_name = st.session_state.get("dataset_name") or "Current dataset"
    dataset_source = st.session_state.get("dataset_source")

    st.subheader("Current Session")
    st.caption("A quick summary of the dataset that is currently loaded into the app.")

    with st.container(border=True):
        st.markdown(f"**Dataset:** `{dataset_name}`")
        st.caption(f"Source: {(dataset_source or 'unknown').replace('_', ' ').title()}")

        session_metrics = st.columns(3)
        session_metrics[0].metric("Rows", f"{len(current_df):,}")
        session_metrics[1].metric("Columns", current_df.shape[1])
        session_metrics[2].metric("Saved Steps", len(log_entries))

    st.caption("Current data preview")
    st.dataframe(current_df.head(10), width="stretch")

    with st.expander("Current Data Types", expanded=False):
        dtype_table = pd.DataFrame({"column": current_df.columns, "dtype": current_df.dtypes.astype(str).values})
        st.dataframe(dtype_table, width="stretch", hide_index=True)
else:
    st.info("Open Upload & Overview to load your own file or one of the bundled sample datasets.")

st.subheader("Included Sample Data")
st.caption("Use the bundled files for quick checks if you do not want to upload your own data yet.")

sample_cols = st.columns(2)
with sample_cols[0]:
    with st.container(border=True):
        st.markdown("#### Retail Sales Sample")
        st.caption("A sample sales dataset for testing profiling, filtering, charting, and export features.")
with sample_cols[1]:
    with st.container(border=True):
        st.markdown("#### HR Dirty Sample")
        st.caption("An HR dataset with missing values, mixed types, and duplicate rows for testing the cleaning workflow.")
