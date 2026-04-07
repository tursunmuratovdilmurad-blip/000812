"""Streamlit entry point and page navigation."""

from __future__ import annotations

import streamlit as st

from utils.ui import apply_shared_styles, render_sidebar_brand


st.set_page_config(
    page_title="AI-Assisted Data Wrangler & Visualizer",
    layout="wide",
)

apply_shared_styles()
render_sidebar_brand()

navigation = st.navigation(
    [
        st.Page("home.py", title="Home", default=True),
        st.Page("pages/1_Upload_Overview.py", title="Upload & Overview"),
        st.Page("pages/2_Cleaning_Preparation.py", title="Cleaning & Preparation"),
        st.Page("pages/3_Visualization_Builder.py", title="Visualization Builder"),
        st.Page("pages/4_Export_Report.py", title="Export & Report"),
    ],
    position="sidebar",
)

navigation.run()
