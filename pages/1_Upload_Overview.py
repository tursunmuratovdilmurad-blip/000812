"""Upload and overview page."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from utils.data_io import list_sample_datasets, load_sample_dataset, load_uploaded_dataset
from utils.profiling import build_profile
from utils.session import get_current_df, has_dataset, init_session_state, reset_session, set_dataset
from utils.ui import apply_shared_styles, render_page_header, render_section_header


init_session_state()
apply_shared_styles()

render_page_header(
    "Upload & Overview",
    "Load a dataset, review its structure, and inspect the starting profile before making any changes.",
    eyebrow="Data Intake",
)

sample_dir = Path(__file__).resolve().parents[1] / "sample_data"

control_col, reset_col = st.columns([4, 1])
with control_col:
    st.write("Supported formats: `CSV`, `XLSX`, and `JSON`.")
with reset_col:
    if st.button("Reset session", width="stretch"):
        reset_session()
        st.rerun()

render_section_header("Load a Dataset", "Upload your own file or start with one of the bundled sample datasets.")
upload_tab, sample_tab = st.tabs(["Upload File", "Sample Datasets"])

with upload_tab:
    uploaded_file = st.file_uploader(
        "Upload a dataset",
        type=["csv", "xlsx", "json"],
        help="Use this to load your own dataset into the app.",
    )
    if uploaded_file is not None and st.button("Load uploaded dataset", type="primary"):
        try:
            dataframe = load_uploaded_dataset(uploaded_file.name, uploaded_file.getvalue())
            set_dataset(dataframe, uploaded_file.name, "uploaded")
            st.success(f"Loaded {uploaded_file.name} successfully.")
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))

with sample_tab:
    sample_paths = list_sample_datasets(str(sample_dir))
    if not sample_paths:
        st.warning("No sample datasets were found in the sample_data folder.")
    else:
        sample_options = {path.name: path for path in sample_paths}
        selected_sample_name = st.selectbox("Choose a bundled sample dataset", options=list(sample_options))
        if st.button("Load selected sample"):
            try:
                sample_df = load_sample_dataset(str(sample_options[selected_sample_name]))
                set_dataset(sample_df, selected_sample_name, "sample")
                st.success(f"Loaded sample dataset: {selected_sample_name}")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

if not has_dataset():
    st.info("No dataset is loaded yet. Use the uploader above or load one of the bundled sample datasets.")
    st.stop()

current_df = get_current_df()
profile = build_profile(current_df)

render_section_header("Dataset Snapshot", "A quick dashboard summary of the dataset currently loaded in the app.")
metric_col_1, metric_col_2, metric_col_3, metric_col_4 = st.columns(4)
metric_col_1.metric("Rows", f"{profile['shape'][0]:,}")
metric_col_2.metric("Columns", profile["shape"][1])
metric_col_3.metric("Duplicate Rows", profile["duplicates_count"])
metric_col_4.metric("Missing Cells", int(current_df.isna().sum().sum()))

st.info(f"Number of columns: {profile['shape'][1]}")

meta_col_1, meta_col_2 = st.columns([2, 3])
with meta_col_1:
    st.write("**Column Names**")
    st.write(", ".join(profile["column_names"]))
with meta_col_2:
    st.write("**Inferred Data Types**")
    st.dataframe(profile["dtypes"], width="stretch", hide_index=True)

render_section_header("Preview", "The first rows of the active dataset.")
st.dataframe(profile["preview"], width="stretch")

render_section_header("Summary Tables", "Review numeric and categorical columns before starting the cleaning workflow.")
summary_col_1, summary_col_2 = st.columns(2)
with summary_col_1:
    st.write("**Numeric Summary Statistics**")
    if profile["numeric_summary"].empty:
        st.info("No numeric columns were detected.")
    else:
        st.dataframe(profile["numeric_summary"], width="stretch", hide_index=True)

with summary_col_2:
    st.write("**Categorical Summary Statistics**")
    if profile["categorical_summary"].empty:
        st.info("No categorical or text columns were detected.")
    else:
        st.dataframe(profile["categorical_summary"], width="stretch", hide_index=True)

render_section_header("Missing Values by Column", "Missing-value counts and percentages for each column.")
st.dataframe(profile["missing_summary"], width="stretch", hide_index=True)
