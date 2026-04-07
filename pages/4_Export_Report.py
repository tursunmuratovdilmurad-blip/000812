"""Export and report page."""

from __future__ import annotations

from datetime import datetime
import json

import pandas as pd
import streamlit as st

from utils.data_io import (
    dataframe_to_csv_bytes,
    dataframe_to_excel_bytes,
    json_to_bytes,
    sanitize_filename,
    text_to_bytes,
)
from utils.session import get_current_df, get_original_df, get_transformation_log, has_dataset, init_session_state
from utils.ui import apply_shared_styles, render_page_header, render_section_header


init_session_state()
apply_shared_styles()


def build_recipe_report() -> dict[str, object]:
    """Build a JSON-safe report describing the current workflow state."""
    original_df = get_original_df()
    current_df = get_current_df()
    transformation_log = get_transformation_log()

    return {
        "dataset_name": st.session_state.get("dataset_name") or "dataset",
        "dataset_source": st.session_state.get("dataset_source"),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "shape_before": {
            "rows": int(original_df.shape[0]),
            "columns": int(original_df.shape[1]),
        },
        "shape_after": {
            "rows": int(current_df.shape[0]),
            "columns": int(current_df.shape[1]),
        },
        "column_names_after": current_df.columns.tolist(),
        "transformation_steps": transformation_log,
    }


def build_markdown_summary(report: dict[str, object]) -> str:
    """Create a human-readable markdown summary of the workflow."""
    lines = [
        "# Transformation Summary",
        "",
        f"- Dataset name: {report['dataset_name']}",
        f"- Dataset source: {report.get('dataset_source') or 'unknown'}",
        f"- Generated at: {report['generated_at']}",
        f"- Shape before: {report['shape_before']['rows']} rows x {report['shape_before']['columns']} columns",
        f"- Shape after: {report['shape_after']['rows']} rows x {report['shape_after']['columns']} columns",
        "",
        "## Transformation Steps",
    ]

    steps = report.get("transformation_steps", [])
    if not steps:
        lines.append("No transformations were applied.")
    else:
        for index, step in enumerate(steps, start=1):
            lines.extend(
                [
                    f"### Step {index}: {step['operation']}",
                    f"- Timestamp: {step['timestamp']}",
                    f"- Affected columns: {', '.join(step['affected_columns']) if step['affected_columns'] else 'None'}",
                    f"- Parameters: {json.dumps(step['parameters'], ensure_ascii=False)}",
                    "",
                ]
            )

    latest_violations_df = st.session_state.get("violations_df")
    lines.append("## Validation")
    if isinstance(latest_violations_df, pd.DataFrame) and not latest_violations_df.empty:
        lines.append(f"Latest violations table rows: {len(latest_violations_df)}")
    else:
        lines.append("No validation violations table is currently stored.")

    return "\n".join(lines)


render_page_header(
    "Export & Report",
    "Download the cleaned dataset, export the transformation recipe, and review the final workflow summary.",
    eyebrow="Outputs",
)

if not has_dataset():
    st.info("Load and optionally transform a dataset before exporting results.")
    st.stop()

current_df = get_current_df()
original_df = get_original_df()
transformation_log = get_transformation_log()
violations_df = st.session_state.get("violations_df")

metric_col_1, metric_col_2, metric_col_3 = st.columns(3)
metric_col_1.metric("Rows Before", f"{len(original_df):,}")
metric_col_2.metric("Rows After", f"{len(current_df):,}")
metric_col_3.metric("Logged Steps", len(transformation_log))

report = build_recipe_report()
markdown_summary = build_markdown_summary(report)
base_filename = sanitize_filename(str(report["dataset_name"]))

render_section_header("Exports", "Download the current dataset and report files from the latest working session.")
export_col_1, export_col_2 = st.columns(2)
with export_col_1:
    st.download_button(
        "Download cleaned dataset (CSV)",
        data=dataframe_to_csv_bytes(current_df),
        file_name=f"{base_filename}_cleaned.csv",
        mime="text/csv",
        width="stretch",
    )
    st.download_button(
        "Download cleaned dataset (Excel)",
        data=dataframe_to_excel_bytes(current_df),
        file_name=f"{base_filename}_cleaned.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width="stretch",
    )

with export_col_2:
    st.download_button(
        "Download transformation report (JSON)",
        data=json_to_bytes(report),
        file_name=f"{base_filename}_recipe.json",
        mime="application/json",
        width="stretch",
    )
    st.download_button(
        "Download transformation summary (Markdown)",
        data=text_to_bytes(markdown_summary),
        file_name=f"{base_filename}_summary.md",
        mime="text/markdown",
        width="stretch",
    )

if isinstance(violations_df, pd.DataFrame) and not violations_df.empty:
    st.download_button(
        "Download latest violations table (CSV)",
        data=dataframe_to_csv_bytes(violations_df),
        file_name=f"{base_filename}_violations.csv",
        mime="text/csv",
        width="stretch",
    )
else:
    st.info("No violations table is available right now. Run a validation rule on the Cleaning page if you want to export one.")

render_section_header("Transformation Log", "Review the step history included in the exported report.")
if transformation_log:
    log_table = pd.DataFrame(transformation_log).copy()
    log_table["parameters"] = log_table["parameters"].apply(lambda value: json.dumps(value, ensure_ascii=False))
    log_table["affected_columns"] = log_table["affected_columns"].apply(lambda value: ", ".join(value))
    st.dataframe(log_table, width="stretch", hide_index=True)
else:
    st.info("The dataset has not been transformed yet, so the export recipe contains no transformation steps.")

with st.expander("Recipe Preview", expanded=False):
    st.json(report)

with st.expander("Markdown Summary Preview", expanded=False):
    st.markdown(markdown_summary)
