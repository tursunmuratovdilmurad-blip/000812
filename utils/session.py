"""Session state helpers for the Streamlit app."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable

import pandas as pd
import streamlit as st


def init_session_state() -> None:
    """Create the session keys used across all pages."""
    defaults: dict[str, Any] = {
        "dataset_name": None,
        "dataset_source": None,
        "original_df": None,
        "current_df": None,
        "history_stack": [],
        "transformation_log": [],
        "violations_df": None,
        "last_preview": None,
    }

    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default.copy() if isinstance(default, list) else default


def _json_safe(value: Any) -> Any:
    """Convert common pandas/numpy values into JSON-friendly Python objects."""
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    return value


def set_dataset(df: pd.DataFrame, dataset_name: str, dataset_source: str) -> None:
    """Reset the app around a newly loaded dataset."""
    clean_df = df.copy(deep=True)
    st.session_state.dataset_name = dataset_name
    st.session_state.dataset_source = dataset_source
    st.session_state.original_df = clean_df.copy(deep=True)
    st.session_state.current_df = clean_df.copy(deep=True)
    st.session_state.history_stack = [clean_df.copy(deep=True)]
    st.session_state.transformation_log = []
    st.session_state.violations_df = None
    st.session_state.last_preview = None


def has_dataset() -> bool:
    """Return True when a working dataframe exists in session state."""
    return isinstance(st.session_state.get("current_df"), pd.DataFrame)


def get_current_df() -> pd.DataFrame | None:
    """Return the current working dataframe."""
    return st.session_state.get("current_df")


def get_original_df() -> pd.DataFrame | None:
    """Return the original uploaded dataframe."""
    return st.session_state.get("original_df")


def get_transformation_log() -> list[dict[str, Any]]:
    """Return the current transformation log."""
    return st.session_state.get("transformation_log", [])


def apply_transformation(
    new_df: pd.DataFrame,
    operation_name: str,
    parameters: dict[str, Any] | None = None,
    affected_columns: Iterable[str] | None = None,
    preview: dict[str, Any] | None = None,
) -> None:
    """Persist a transformed dataframe and append a structured log entry."""
    if not isinstance(new_df, pd.DataFrame):
        raise ValueError("Transformation result must be a pandas DataFrame.")

    safe_df = new_df.copy(deep=True)
    st.session_state.current_df = safe_df
    st.session_state.history_stack.append(safe_df.copy(deep=True))

    log_entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "operation": operation_name,
        "parameters": _json_safe(parameters or {}),
        "affected_columns": list(affected_columns or []),
    }
    st.session_state.transformation_log.append(log_entry)
    st.session_state.last_preview = preview


def undo_last_step() -> bool:
    """Undo the most recent transformation if possible."""
    history_stack: list[pd.DataFrame] = st.session_state.get("history_stack", [])
    if len(history_stack) <= 1:
        return False

    history_stack.pop()
    st.session_state.current_df = history_stack[-1].copy(deep=True)

    transformation_log = st.session_state.get("transformation_log", [])
    if transformation_log:
        transformation_log.pop()

    st.session_state.last_preview = None
    st.session_state.violations_df = None
    return True


def reset_to_original() -> bool:
    """Reset the working dataframe to the original uploaded version."""
    original_df = get_original_df()
    if original_df is None:
        return False

    st.session_state.current_df = original_df.copy(deep=True)
    st.session_state.history_stack = [original_df.copy(deep=True)]
    st.session_state.transformation_log = []
    st.session_state.violations_df = None
    st.session_state.last_preview = None
    return True


def reset_session() -> None:
    """Clear all dataset-related keys from session state."""
    for key in [
        "dataset_name",
        "dataset_source",
        "original_df",
        "current_df",
        "history_stack",
        "transformation_log",
        "violations_df",
        "last_preview",
    ]:
        st.session_state.pop(key, None)
    init_session_state()


def set_violations_df(violations_df: pd.DataFrame | None) -> None:
    """Store the latest validation violations table."""
    st.session_state.violations_df = violations_df.copy(deep=True) if isinstance(violations_df, pd.DataFrame) else None
