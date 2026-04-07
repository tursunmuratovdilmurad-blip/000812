"""Cleaning and transformation helpers."""

from __future__ import annotations

import ast
import re
from typing import Any, Iterable

import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype


def _require_columns(df: pd.DataFrame, columns: Iterable[str]) -> list[str]:
    selected_columns = [column for column in columns if column]
    missing_columns = [column for column in selected_columns if column not in df.columns]
    if missing_columns:
        raise ValueError(f"Selected columns are not available: {', '.join(missing_columns)}")
    return selected_columns


def missing_value_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize missing values by column."""
    missing_counts = df.isna().sum()
    return pd.DataFrame(
        {
            "column": df.columns,
            "missing_count": missing_counts.values,
            "missing_percent": ((missing_counts / len(df)) * 100).round(2).values,
        }
    ).sort_values(["missing_count", "column"], ascending=[False, True], ignore_index=True)


def drop_rows_with_missing(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Drop rows with missing values in the selected columns."""
    selected_columns = _require_columns(df, columns)
    if not selected_columns:
        raise ValueError("Select at least one column to drop missing rows.")
    return df.dropna(subset=selected_columns).copy()


def drop_columns_by_missing_threshold(df: pd.DataFrame, threshold_percent: float) -> tuple[pd.DataFrame, list[str]]:
    """Drop columns whose missing percentage is above the chosen threshold."""
    if threshold_percent < 0 or threshold_percent > 100:
        raise ValueError("Missing threshold must be between 0 and 100.")

    missing_percent = (df.isna().mean() * 100).round(2)
    columns_to_drop = missing_percent[missing_percent > threshold_percent].index.tolist()
    return df.drop(columns=columns_to_drop).copy(), columns_to_drop


def fill_missing_values(
    df: pd.DataFrame,
    columns: list[str],
    strategy: str,
    constant_value: Any | None = None,
) -> pd.DataFrame:
    """Fill missing values using the selected strategy."""
    selected_columns = _require_columns(df, columns)
    if not selected_columns:
        raise ValueError("Select at least one column to fill.")

    result = df.copy()

    if strategy == "ffill":
        result[selected_columns] = result[selected_columns].ffill()
        return result

    if strategy == "bfill":
        result[selected_columns] = result[selected_columns].bfill()
        return result

    for column in selected_columns:
        series = result[column]

        if strategy == "constant":
            result[column] = series.fillna(constant_value)
        elif strategy == "mean":
            if not is_numeric_dtype(series):
                raise ValueError(f"Column '{column}' is not numeric, so mean fill cannot be used.")
            result[column] = series.fillna(series.mean())
        elif strategy == "median":
            if not is_numeric_dtype(series):
                raise ValueError(f"Column '{column}' is not numeric, so median fill cannot be used.")
            result[column] = series.fillna(series.median())
        elif strategy in {"mode", "most_frequent"}:
            mode = series.mode(dropna=True)
            if mode.empty:
                raise ValueError(f"Column '{column}' has no non-null values available for mode fill.")
            result[column] = series.fillna(mode.iloc[0])
        else:
            raise ValueError("Unsupported fill strategy selected.")

    return result


def detect_duplicates(df: pd.DataFrame, subset: list[str] | None = None) -> pd.Series:
    """Return a boolean mask of duplicate rows."""
    selected_subset = _require_columns(df, subset or [])
    return df.duplicated(subset=selected_subset or None, keep=False)


def duplicate_groups_table(df: pd.DataFrame, subset: list[str] | None = None) -> pd.DataFrame:
    """Return a table of duplicate rows grouped by the chosen subset."""
    duplicate_mask = detect_duplicates(df, subset)
    if not duplicate_mask.any():
        return pd.DataFrame()

    selected_subset = _require_columns(df, subset or [])
    key_columns = selected_subset if selected_subset else list(df.columns)

    duplicate_rows = df.loc[duplicate_mask].copy()
    duplicate_rows.insert(0, "row_index", duplicate_rows.index)
    duplicate_rows.insert(
        1,
        "duplicate_group",
        duplicate_rows[key_columns].astype(str).agg(" | ".join, axis=1),
    )
    return duplicate_rows.sort_values(["duplicate_group", "row_index"]).reset_index(drop=True)


def remove_duplicates(df: pd.DataFrame, subset: list[str] | None = None, keep: str = "first") -> pd.DataFrame:
    """Remove duplicate rows while keeping the first or last occurrence."""
    if keep not in {"first", "last"}:
        raise ValueError("Duplicate keep strategy must be 'first' or 'last'.")
    selected_subset = _require_columns(df, subset or [])
    return df.drop_duplicates(subset=selected_subset or None, keep=keep).copy()


def clean_numeric_strings(
    series: pd.Series,
    remove_commas: bool = True,
    remove_currency_symbols: bool = True,
    strip_spaces: bool = True,
) -> pd.Series:
    """Clean typical dirty numeric strings before conversion."""
    if is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce")

    cleaned = series.astype("string")

    if strip_spaces:
        cleaned = cleaned.str.strip()

    if remove_commas:
        cleaned = cleaned.str.replace(",", "", regex=False)

    if remove_currency_symbols:
        cleaned = cleaned.str.replace("[\\u0024\\u20AC\\u00A3\\u00A5\\u20B9]", "", regex=True)

    cleaned = cleaned.str.replace(r"\s+", "", regex=True)
    cleaned = cleaned.replace({"": pd.NA, "nan": pd.NA, "None": pd.NA, "<NA>": pd.NA})
    return pd.to_numeric(cleaned, errors="coerce")


def convert_columns_to_numeric(
    df: pd.DataFrame,
    columns: list[str],
    remove_commas: bool = True,
    remove_currency_symbols: bool = True,
    strip_spaces: bool = True,
) -> pd.DataFrame:
    """Convert selected columns to numeric safely."""
    selected_columns = _require_columns(df, columns)
    if not selected_columns:
        raise ValueError("Select at least one column to convert to numeric.")

    result = df.copy()
    for column in selected_columns:
        result[column] = clean_numeric_strings(
            result[column],
            remove_commas=remove_commas,
            remove_currency_symbols=remove_currency_symbols,
            strip_spaces=strip_spaces,
        )
    return result


def convert_columns_to_category(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Convert selected columns to categorical dtype."""
    selected_columns = _require_columns(df, columns)
    if not selected_columns:
        raise ValueError("Select at least one column to convert to categorical.")

    result = df.copy()
    for column in selected_columns:
        result[column] = result[column].astype("category")
    return result


def convert_columns_to_datetime(df: pd.DataFrame, columns: list[str], date_format: str | None = None) -> pd.DataFrame:
    """Convert selected columns to datetime using optional format hints."""
    selected_columns = _require_columns(df, columns)
    if not selected_columns:
        raise ValueError("Select at least one column to convert to datetime.")

    result = df.copy()
    for column in selected_columns:
        result[column] = pd.to_datetime(result[column], format=date_format or None, errors="coerce")
    return result


def clean_categorical_text(df: pd.DataFrame, columns: list[str], operation: str) -> pd.DataFrame:
    """Apply whitespace or casing cleanup to selected columns."""
    selected_columns = _require_columns(df, columns)
    if not selected_columns:
        raise ValueError("Select at least one column for categorical cleanup.")

    result = df.copy()
    for column in selected_columns:
        text_series = result[column].astype("string")
        if operation == "trim":
            result[column] = text_series.str.strip()
        elif operation == "lower":
            result[column] = text_series.str.lower()
        elif operation == "title":
            result[column] = text_series.str.title()
        else:
            raise ValueError("Unsupported categorical text operation.")
    return result


def apply_category_mapping(df: pd.DataFrame, column: str, mapping: dict[str, str]) -> pd.DataFrame:
    """Replace values using a user-defined mapping."""
    _require_columns(df, [column])
    usable_mapping = {old: new for old, new in mapping.items() if new is not None and str(new).strip() != ""}
    if not usable_mapping:
        raise ValueError("Provide at least one replacement value in the mapping table.")

    result = df.copy()
    result[column] = result[column].replace(usable_mapping)
    return result


def group_rare_categories(df: pd.DataFrame, column: str, min_frequency: int, other_label: str = "Other") -> pd.DataFrame:
    """Group low-frequency categories into an 'Other' label."""
    _require_columns(df, [column])
    if min_frequency < 1:
        raise ValueError("Rare category threshold must be at least 1.")

    result = df.copy()
    counts = result[column].value_counts(dropna=False)
    rare_values = counts[counts < min_frequency].index
    result[column] = result[column].where(~result[column].isin(rare_values), other_label)
    return result


def one_hot_encode_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Apply one-hot encoding to selected columns."""
    selected_columns = _require_columns(df, columns)
    if not selected_columns:
        raise ValueError("Select at least one column to one-hot encode.")
    return pd.get_dummies(df.copy(), columns=selected_columns)


def iqr_outlier_summary(df: pd.DataFrame, columns: list[str], multiplier: float = 1.5) -> pd.DataFrame:
    """Summarize outliers using the IQR rule."""
    selected_columns = _require_columns(df, columns)
    rows: list[dict[str, Any]] = []

    for column in selected_columns:
        series = pd.to_numeric(df[column], errors="coerce").dropna()
        if series.empty:
            continue
        q1 = float(series.quantile(0.25))
        q3 = float(series.quantile(0.75))
        iqr = q3 - q1
        lower_bound = q1 - (multiplier * iqr)
        upper_bound = q3 + (multiplier * iqr)
        mask = (series < lower_bound) | (series > upper_bound)
        rows.append(
            {
                "column": column,
                "q1": round(q1, 4),
                "q3": round(q3, 4),
                "iqr": round(iqr, 4),
                "lower_bound": round(lower_bound, 4),
                "upper_bound": round(upper_bound, 4),
                "outlier_count": int(mask.sum()),
                "outlier_percent": round((mask.sum() / len(series)) * 100, 2),
            }
        )

    return pd.DataFrame(rows)


def zscore_outlier_summary(df: pd.DataFrame, columns: list[str], threshold: float = 3.0) -> pd.DataFrame:
    """Summarize outliers using a z-score threshold."""
    selected_columns = _require_columns(df, columns)
    rows: list[dict[str, Any]] = []

    for column in selected_columns:
        series = pd.to_numeric(df[column], errors="coerce").dropna()
        if series.empty:
            continue
        std = series.std()
        if std == 0 or pd.isna(std):
            outlier_count = 0
        else:
            z_scores = (series - series.mean()) / std
            outlier_count = int((z_scores.abs() > threshold).sum())

        rows.append(
            {
                "column": column,
                "mean": round(float(series.mean()), 4),
                "std": round(float(std), 4) if not pd.isna(std) else np.nan,
                "zscore_threshold": threshold,
                "outlier_count": outlier_count,
            }
        )

    return pd.DataFrame(rows)


def cap_outliers_quantiles(
    df: pd.DataFrame,
    columns: list[str],
    lower_quantile: float,
    upper_quantile: float,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Cap selected numeric columns at the chosen quantiles."""
    selected_columns = _require_columns(df, columns)
    if not selected_columns:
        raise ValueError("Select at least one numeric column to cap.")
    if not 0 <= lower_quantile < upper_quantile <= 1:
        raise ValueError("Choose quantiles between 0 and 1, with lower less than upper.")

    result = df.copy()
    capped_counts: dict[str, int] = {}

    for column in selected_columns:
        numeric_series = pd.to_numeric(result[column], errors="coerce")
        if numeric_series.dropna().empty:
            raise ValueError(f"Column '{column}' does not contain numeric values to cap.")
        lower_value = numeric_series.quantile(lower_quantile)
        upper_value = numeric_series.quantile(upper_quantile)
        capped_mask = numeric_series.notna() & ((numeric_series < lower_value) | (numeric_series > upper_value))
        capped_counts[column] = int(capped_mask.sum())
        result[column] = numeric_series.clip(lower=lower_value, upper=upper_value)

    return result, capped_counts


def remove_outlier_rows_iqr(
    df: pd.DataFrame,
    columns: list[str],
    multiplier: float = 1.5,
) -> tuple[pd.DataFrame, int]:
    """Remove rows containing IQR outliers in any selected column."""
    selected_columns = _require_columns(df, columns)
    if not selected_columns:
        raise ValueError("Select at least one numeric column for outlier removal.")

    overall_mask = pd.Series(False, index=df.index)
    for column in selected_columns:
        series = pd.to_numeric(df[column], errors="coerce")
        non_null = series.dropna()
        if non_null.empty:
            continue
        q1 = non_null.quantile(0.25)
        q3 = non_null.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - (multiplier * iqr)
        upper_bound = q3 + (multiplier * iqr)
        overall_mask |= series.notna() & ((series < lower_bound) | (series > upper_bound))

    return df.loc[~overall_mask].copy(), int(overall_mask.sum())


def summarize_numeric_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Return basic before/after stats for selected numeric columns."""
    selected_columns = [column for column in columns if column in df.columns and is_numeric_dtype(df[column])]
    if not selected_columns:
        return pd.DataFrame(columns=["column", "count", "mean", "std", "min", "median", "max"])

    stats = (
        df[selected_columns]
        .agg(["count", "mean", "std", "min", "median", "max"])
        .transpose()
        .reset_index()
        .rename(columns={"index": "column"})
    )
    return stats.round(4)


def scale_columns(df: pd.DataFrame, columns: list[str], method: str) -> pd.DataFrame:
    """Scale numeric columns using Min-Max or Z-score standardization."""
    selected_columns = _require_columns(df, columns)
    if not selected_columns:
        raise ValueError("Select at least one numeric column to scale.")

    result = df.copy()
    for column in selected_columns:
        series = pd.to_numeric(result[column], errors="coerce")
        if series.dropna().empty:
            raise ValueError(f"Column '{column}' is not numeric enough to scale.")

        if method == "minmax":
            min_value = series.min()
            max_value = series.max()
            if pd.isna(min_value) or pd.isna(max_value):
                raise ValueError(f"Column '{column}' cannot be scaled because it only contains missing values.")
            if max_value == min_value:
                result[column] = 0.0
            else:
                result[column] = (series - min_value) / (max_value - min_value)
        elif method == "zscore":
            std_value = series.std()
            if pd.isna(std_value):
                raise ValueError(f"Column '{column}' cannot be standardized because its standard deviation is missing.")
            if std_value == 0:
                result[column] = 0.0
            else:
                result[column] = (series - series.mean()) / std_value
        else:
            raise ValueError("Unsupported scaling method.")

    return result


def rename_columns(df: pd.DataFrame, rename_map: dict[str, str]) -> pd.DataFrame:
    """Rename columns after validating duplicate and empty names."""
    usable_mapping = {old: new for old, new in rename_map.items() if old != new}
    if not usable_mapping:
        raise ValueError("Enter at least one new column name before applying rename.")

    new_names = [str(name).strip() for name in usable_mapping.values()]
    if any(not name for name in new_names):
        raise ValueError("Column names cannot be blank.")

    future_columns = [usable_mapping.get(column, column) for column in df.columns]
    if len(future_columns) != len(set(future_columns)):
        raise ValueError("Renaming would create duplicate column names.")

    return df.rename(columns=usable_mapping).copy()


def drop_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Drop selected columns."""
    selected_columns = _require_columns(df, columns)
    if not selected_columns:
        raise ValueError("Select at least one column to drop.")
    return df.drop(columns=selected_columns).copy()


def build_column_alias_map(columns: Iterable[str]) -> dict[str, str]:
    """Create safe formula aliases for dataframe columns."""
    alias_map: dict[str, str] = {}
    used_aliases: set[str] = set()

    for column in columns:
        base = re.sub(r"\W+", "_", str(column).strip().lower()).strip("_")
        if not base:
            base = "column"
        if base[0].isdigit():
            base = f"col_{base}"

        alias = base
        counter = 2
        while alias in used_aliases:
            alias = f"{base}_{counter}"
            counter += 1

        alias_map[alias] = str(column)
        used_aliases.add(alias)

        if str(column).isidentifier() and str(column) not in used_aliases and str(column) not in alias_map:
            alias_map[str(column)] = str(column)
            used_aliases.add(str(column))

    return alias_map


class _SafeFormulaEvaluator:
    """Restricted AST evaluator for simple dataframe formulas."""

    VECTOR_FUNCTIONS = {
        "log": np.log,
        "sqrt": np.sqrt,
        "abs": np.abs,
        "exp": np.exp,
    }

    REDUCER_FUNCTIONS = {
        "mean": lambda value: float(pd.Series(value).mean()),
        "median": lambda value: float(pd.Series(value).median()),
        "min": lambda value: float(pd.Series(value).min()),
        "max": lambda value: float(pd.Series(value).max()),
        "std": lambda value: float(pd.Series(value).std()),
    }

    def __init__(self, df: pd.DataFrame, alias_map: dict[str, str]) -> None:
        self.df = df
        self.alias_map = alias_map

    def evaluate(self, formula: str) -> pd.Series:
        """Evaluate a formula string into a pandas Series."""
        try:
            tree = ast.parse(formula, mode="eval")
        except SyntaxError as exc:
            raise ValueError("The formula could not be parsed. Check the syntax and try again.") from exc

        result = self._eval_node(tree.body)
        if isinstance(result, pd.Series):
            return result.reindex(self.df.index)
        if np.isscalar(result):
            return pd.Series([result] * len(self.df), index=self.df.index)
        raise ValueError("Formula result must be a numeric scalar or a column-based expression.")

    def _eval_node(self, node: ast.AST) -> Any:
        if isinstance(node, ast.BinOp):
            return self._eval_binop(node)
        if isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            if isinstance(node.op, ast.UAdd):
                return +operand
            if isinstance(node.op, ast.USub):
                return -operand
            raise ValueError("Only + and - unary operators are allowed.")
        if isinstance(node, ast.Call):
            return self._eval_call(node)
        if isinstance(node, ast.Name):
            if node.id in self.alias_map:
                return self.df[self.alias_map[node.id]]
            raise ValueError(f"Unknown formula reference: {node.id}")
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("Only numeric constants are allowed in formulas.")
        raise ValueError("The formula uses a blocked expression. Use arithmetic with approved functions only.")

    def _eval_binop(self, node: ast.BinOp) -> Any:
        left = self._eval_node(node.left)
        right = self._eval_node(node.right)

        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
        if isinstance(node.op, ast.Pow):
            return left**right
        raise ValueError("Only +, -, *, /, and ** operations are allowed.")

    def _eval_call(self, node: ast.Call) -> Any:
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only named functions are allowed in formulas.")

        function_name = node.func.id
        if function_name == "round":
            if len(node.args) not in {1, 2}:
                raise ValueError("round() accepts one or two arguments.")
            value = self._eval_node(node.args[0])
            decimals = int(self._eval_node(node.args[1])) if len(node.args) == 2 else 0
            return np.round(value, decimals)

        if function_name in self.VECTOR_FUNCTIONS:
            if len(node.args) != 1:
                raise ValueError(f"{function_name}() expects exactly one argument.")
            return self.VECTOR_FUNCTIONS[function_name](self._eval_node(node.args[0]))

        if function_name in self.REDUCER_FUNCTIONS:
            if len(node.args) != 1:
                raise ValueError(f"{function_name}() expects exactly one argument.")
            return self.REDUCER_FUNCTIONS[function_name](self._eval_node(node.args[0]))

        raise ValueError(f"Function '{function_name}' is not allowed.")


def create_formula_column(
    df: pd.DataFrame,
    new_column_name: str,
    formula: str,
    alias_map: dict[str, str] | None = None,
) -> tuple[pd.DataFrame, dict[str, str]]:
    """Create a new column using a restricted formula expression."""
    if not new_column_name.strip():
        raise ValueError("New column name cannot be blank.")
    if new_column_name in df.columns:
        raise ValueError("Choose a new column name that does not already exist.")

    aliases = alias_map or build_column_alias_map(df.columns)
    evaluator = _SafeFormulaEvaluator(df, aliases)
    result = df.copy()
    try:
        result[new_column_name] = evaluator.evaluate(formula)
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(
            "Formula evaluation failed. Make sure arithmetic columns are numeric and the expression is valid."
        ) from exc
    return result, aliases


def bin_numeric_column(
    df: pd.DataFrame,
    source_column: str,
    new_column_name: str,
    method: str,
    bins: int,
) -> pd.DataFrame:
    """Bin a numeric column into categories."""
    _require_columns(df, [source_column])
    if not new_column_name.strip():
        raise ValueError("Binned column name cannot be blank.")
    if new_column_name in df.columns:
        raise ValueError("Choose a new column name for the binned output.")
    if bins < 2:
        raise ValueError("Use at least 2 bins.")

    numeric_series = pd.to_numeric(df[source_column], errors="coerce")
    if numeric_series.dropna().empty:
        raise ValueError(f"Column '{source_column}' does not contain numeric values to bin.")

    result = df.copy()
    if method == "equal_width":
        result[new_column_name] = pd.cut(numeric_series, bins=bins, duplicates="drop").astype("string")
    elif method == "quantile":
        result[new_column_name] = pd.qcut(numeric_series, q=bins, duplicates="drop").astype("string")
    else:
        raise ValueError("Unsupported binning method.")
    return result
