"""Data profiling helpers for overview and reporting."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import streamlit as st


def _build_categorical_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Create a compact summary for non-numeric columns."""
    non_numeric = df.select_dtypes(exclude=[np.number])
    if non_numeric.empty:
        return pd.DataFrame(columns=["column", "non_null", "unique", "most_frequent", "top_frequency", "sample_values"])

    rows: list[dict[str, Any]] = []
    for column in non_numeric.columns:
        series = non_numeric[column]
        non_null = series.dropna()
        mode = non_null.mode()
        top_value = mode.iloc[0] if not mode.empty else None
        top_frequency = int((non_null == top_value).sum()) if top_value is not None else 0
        sample_values = ", ".join(non_null.astype(str).unique()[:5])
        rows.append(
            {
                "column": column,
                "non_null": int(series.notna().sum()),
                "unique": int(non_null.nunique(dropna=True)),
                "most_frequent": top_value,
                "top_frequency": top_frequency,
                "sample_values": sample_values,
            }
        )

    return pd.DataFrame(rows)


@st.cache_data(show_spinner=False)
def build_profile(df: pd.DataFrame) -> dict[str, Any]:
    """Generate reusable profile tables for the uploaded dataset."""
    numeric_df = df.select_dtypes(include=[np.number])
    numeric_summary = (
        numeric_df.describe(percentiles=[0.25, 0.5, 0.75]).transpose().reset_index().rename(columns={"index": "column"})
        if not numeric_df.empty
        else pd.DataFrame()
    )

    missing_counts = df.isna().sum()
    missing_summary = pd.DataFrame(
        {
            "column": df.columns,
            "missing_count": missing_counts.values,
            "missing_percent": ((missing_counts / len(df)) * 100).round(2).values,
        }
    ).sort_values(["missing_count", "column"], ascending=[False, True], ignore_index=True)

    dtype_table = pd.DataFrame({"column": df.columns, "dtype": df.dtypes.astype(str).values})

    return {
        "shape": df.shape,
        "column_names": list(df.columns),
        "dtypes": dtype_table,
        "numeric_summary": numeric_summary,
        "categorical_summary": _build_categorical_summary(df),
        "missing_summary": missing_summary,
        "duplicates_count": int(df.duplicated().sum()),
        "preview": df.head(10),
    }
