"""Validation rule helpers."""

from __future__ import annotations

from typing import Iterable

import pandas as pd
from pandas.api.types import is_numeric_dtype


def _require_columns(df: pd.DataFrame, columns: Iterable[str]) -> list[str]:
    selected_columns = [column for column in columns if column]
    missing_columns = [column for column in selected_columns if column not in df.columns]
    if missing_columns:
        raise ValueError(f"Selected columns are not available: {', '.join(missing_columns)}")
    return selected_columns


def _finalize_violation_table(
    source_df: pd.DataFrame,
    mask: pd.Series,
    column: str,
    rule_name: str,
    detail: str,
) -> pd.DataFrame:
    if not mask.any():
        return pd.DataFrame()

    violations = source_df.loc[mask].copy()
    violations.insert(0, "row_index", violations.index)
    violations.insert(1, "column", column)
    violations.insert(2, "rule", rule_name)
    violations.insert(3, "details", detail)
    violations.insert(4, "offending_value", source_df.loc[mask, column].astype("string").values)
    return violations.reset_index(drop=True)


def validate_numeric_range(
    df: pd.DataFrame,
    column: str,
    min_value: float | None,
    max_value: float | None,
) -> pd.DataFrame:
    """Return rows where a numeric value falls outside a chosen range."""
    _require_columns(df, [column])
    if not is_numeric_dtype(df[column]):
        raise ValueError(f"Column '{column}' is not numeric.")
    if min_value is None and max_value is None:
        raise ValueError("Provide at least a minimum or maximum value.")

    numeric_series = pd.to_numeric(df[column], errors="coerce")
    mask = pd.Series(False, index=df.index)
    detail_parts: list[str] = []

    if min_value is not None:
        mask |= numeric_series < min_value
        detail_parts.append(f"value < {min_value}")
    if max_value is not None:
        mask |= numeric_series > max_value
        detail_parts.append(f"value > {max_value}")

    detail = " or ".join(detail_parts)
    return _finalize_violation_table(df, mask, column, "numeric_range", detail)


def validate_allowed_categories(df: pd.DataFrame, column: str, allowed_values: list[str]) -> pd.DataFrame:
    """Return rows containing categories outside the allowed list."""
    _require_columns(df, [column])
    usable_values = [value for value in allowed_values if value.strip()]
    if not usable_values:
        raise ValueError("Provide at least one allowed category.")

    mask = df[column].notna() & ~df[column].astype("string").isin(pd.Series(usable_values, dtype="string"))
    detail = f"allowed values: {', '.join(usable_values)}"
    return _finalize_violation_table(df, mask, column, "allowed_categories", detail)


def validate_non_null(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Return rows where selected columns are null."""
    selected_columns = _require_columns(df, columns)
    if not selected_columns:
        raise ValueError("Select at least one column for the non-null check.")

    tables: list[pd.DataFrame] = []
    for column in selected_columns:
        mask = df[column].isna()
        tables.append(_finalize_violation_table(df, mask, column, "non_null", "value is null"))

    non_empty_tables = [table for table in tables if not table.empty]
    if not non_empty_tables:
        return pd.DataFrame()
    return pd.concat(non_empty_tables, ignore_index=True)
