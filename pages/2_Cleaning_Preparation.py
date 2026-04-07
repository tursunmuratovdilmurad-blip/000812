"""Cleaning and preparation studio page."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import streamlit as st

from utils.session import (
    apply_transformation,
    get_current_df,
    get_transformation_log,
    has_dataset,
    init_session_state,
    reset_to_original,
    set_violations_df,
    undo_last_step,
)
from utils.transforms import (
    apply_category_mapping,
    bin_numeric_column,
    build_column_alias_map,
    cap_outliers_quantiles,
    clean_categorical_text,
    convert_columns_to_category,
    convert_columns_to_datetime,
    convert_columns_to_numeric,
    create_formula_column,
    detect_duplicates,
    drop_columns,
    drop_columns_by_missing_threshold,
    drop_rows_with_missing,
    duplicate_groups_table,
    fill_missing_values,
    group_rare_categories,
    iqr_outlier_summary,
    missing_value_summary,
    one_hot_encode_columns,
    remove_duplicates,
    remove_outlier_rows_iqr,
    rename_columns,
    scale_columns,
    summarize_numeric_columns,
    zscore_outlier_summary,
)
from utils.validation import validate_allowed_categories, validate_non_null, validate_numeric_range
from utils.ui import apply_shared_styles, render_page_header, render_section_header


init_session_state()
apply_shared_styles()


def build_preview(
    before_df: pd.DataFrame,
    after_df: pd.DataFrame,
    operation_name: str,
    affected_columns: list[str],
    extra: dict[str, object] | None = None,
) -> dict[str, object]:
    """Create a reusable before/after preview payload for the UI."""
    before_columns = [column for column in affected_columns if column in before_df.columns][:6]
    after_columns = [column for column in affected_columns if column in after_df.columns][:6]

    if not before_columns:
        before_columns = list(before_df.columns[: min(6, len(before_df.columns))])
    if not after_columns:
        after_columns = list(after_df.columns[: min(6, len(after_df.columns))])

    return {
        "operation": operation_name,
        "rows_before": len(before_df),
        "rows_after": len(after_df),
        "affected_columns": affected_columns,
        "before_preview": before_df[before_columns].head(5),
        "after_preview": after_df[after_columns].head(5),
        "extra": extra or {},
    }


def commit_change(
    before_df: pd.DataFrame,
    after_df: pd.DataFrame,
    operation_name: str,
    parameters: dict[str, object],
    affected_columns: list[str],
    extra: dict[str, object] | None = None,
) -> None:
    """Persist a successful transformation and rerun the page."""
    preview = build_preview(before_df, after_df, operation_name, affected_columns, extra=extra)
    apply_transformation(after_df, operation_name, parameters, affected_columns, preview)
    st.rerun()


def render_last_preview() -> None:
    """Show the most recent transformation impact."""
    preview = st.session_state.get("last_preview")
    if not preview:
        return

    st.success(f"Last completed step: {preview['operation']}")
    metric_col_1, metric_col_2, metric_col_3 = st.columns(3)
    metric_col_1.metric("Rows Before", f"{preview['rows_before']:,}")
    metric_col_2.metric("Rows After", f"{preview['rows_after']:,}")
    metric_col_3.metric("Row Change", f"{preview['rows_after'] - preview['rows_before']:,}")
    st.caption(f"Affected columns: {', '.join(preview['affected_columns']) if preview['affected_columns'] else 'None'}")

    preview_col_1, preview_col_2 = st.columns(2)
    with preview_col_1:
        st.write("**Before Preview**")
        st.dataframe(preview["before_preview"], width="stretch")
    with preview_col_2:
        st.write("**After Preview**")
        st.dataframe(preview["after_preview"], width="stretch")

    for label, value in preview.get("extra", {}).items():
        pretty_label = label.replace("_", " ").title()
        if isinstance(value, pd.DataFrame):
            with st.expander(pretty_label, expanded=False):
                st.dataframe(value, width="stretch", hide_index=True)
        else:
            st.write(f"**{pretty_label}:** {value}")


render_page_header(
    "Cleaning & Preparation",
    "Apply cleaning steps carefully, review the impact after each change, and keep the workflow reversible with undo and reset.",
    eyebrow="Preparation Studio",
)

if not has_dataset():
    st.info("Load a dataset on the Upload & Overview page before using the cleaning studio.")
    st.stop()

current_df = get_current_df()

render_section_header("Working Summary", "Track the current dataset size and the number of logged transformations.")
metric_col_1, metric_col_2, metric_col_3 = st.columns(3)
metric_col_1.metric("Rows", f"{len(current_df):,}")
metric_col_2.metric("Columns", current_df.shape[1])
metric_col_3.metric("Logged Steps", len(get_transformation_log()))

action_col_1, action_col_2 = st.columns(2)
with action_col_1:
    if st.button("Undo last step", width="stretch"):
        if undo_last_step():
            st.rerun()
        st.warning("There is no transformation to undo yet.")
with action_col_2:
    if st.button("Reset all transformations", width="stretch"):
        if reset_to_original():
            st.rerun()
        st.warning("There is no original dataset to reset to.")

render_last_preview()

with st.expander("Transformation Log", expanded=False):
    transformation_log = get_transformation_log()
    if not transformation_log:
        st.info("No transformations have been applied yet.")
    else:
        log_table = pd.DataFrame(transformation_log).copy()
        log_table["parameters"] = log_table["parameters"].apply(lambda value: json.dumps(value, ensure_ascii=False))
        log_table["affected_columns"] = log_table["affected_columns"].apply(lambda value: ", ".join(value))
        st.dataframe(log_table, width="stretch", hide_index=True)

render_section_header("Cleaning Tools", "Use the tabs below to handle missing values, duplicates, data types, categories, numeric cleanup, and validation rules.")
tab_missing, tab_duplicates, tab_types, tab_categories, tab_numeric, tab_scaling, tab_columns, tab_validation = st.tabs(
    [
        "Missing Values",
        "Duplicates",
        "Data Types",
        "Categorical Tools",
        "Numeric Cleaning",
        "Scaling",
        "Column Operations",
        "Validation",
    ]
)

with tab_missing:
    st.write("**Missing Value Summary**")
    st.dataframe(missing_value_summary(current_df), width="stretch", hide_index=True)

    with st.form("drop_missing_rows_form"):
        drop_missing_columns = st.multiselect("Drop rows with missing values in these columns", current_df.columns.tolist())
        submit_drop_rows = st.form_submit_button("Drop rows with missing values")
        if submit_drop_rows:
            try:
                after_df = drop_rows_with_missing(current_df, drop_missing_columns)
                commit_change(
                    current_df,
                    after_df,
                    "drop_rows_with_missing",
                    {"columns": drop_missing_columns},
                    drop_missing_columns,
                )
            except ValueError as exc:
                st.error(str(exc))

    with st.form("drop_sparse_columns_form"):
        missing_threshold = st.slider("Drop columns above this missing percentage", min_value=0, max_value=100, value=40)
        submit_drop_sparse = st.form_submit_button("Drop sparse columns")
        if submit_drop_sparse:
            try:
                after_df, dropped_columns = drop_columns_by_missing_threshold(current_df, float(missing_threshold))
                if not dropped_columns:
                    st.info("No columns exceed the chosen missing-value threshold.")
                else:
                    commit_change(
                        current_df,
                        after_df,
                        "drop_columns_by_missing_threshold",
                        {"threshold_percent": missing_threshold},
                        dropped_columns,
                    )
            except ValueError as exc:
                st.error(str(exc))

    fill_strategy_options = {
        "Fill with constant": "constant",
        "Fill with mean": "mean",
        "Fill with median": "median",
        "Fill with mode": "mode",
        "Fill categorical with most frequent": "most_frequent",
        "Forward fill": "ffill",
        "Backward fill": "bfill",
    }
    with st.form("fill_missing_values_form"):
        fill_columns = st.multiselect("Columns to fill", current_df.columns.tolist())
        fill_strategy_label = st.selectbox("Fill strategy", list(fill_strategy_options))
        constant_value = st.text_input("Constant value", value="", help="Used only for the constant fill strategy.")
        submit_fill = st.form_submit_button("Apply missing value fill")
        if submit_fill:
            try:
                after_df = fill_missing_values(
                    current_df,
                    fill_columns,
                    fill_strategy_options[fill_strategy_label],
                    constant_value if fill_strategy_options[fill_strategy_label] == "constant" else None,
                )
                commit_change(
                    current_df,
                    after_df,
                    "fill_missing_values",
                    {"columns": fill_columns, "strategy": fill_strategy_options[fill_strategy_label]},
                    fill_columns,
                )
            except ValueError as exc:
                st.error(str(exc))

with tab_duplicates:
    st.write("**Duplicate Detection**")
    full_duplicate_count = int(current_df.duplicated().sum())
    subset_columns = st.multiselect("Subset columns for duplicate checking", current_df.columns.tolist(), key="duplicate_subset")
    subset_duplicate_count = int(current_df.duplicated(subset=subset_columns or None).sum())

    duplicate_metric_col_1, duplicate_metric_col_2 = st.columns(2)
    duplicate_metric_col_1.metric("Full-row duplicates", full_duplicate_count)
    duplicate_metric_col_2.metric("Subset duplicates", subset_duplicate_count)

    if st.button("Show duplicate groups"):
        groups_df = duplicate_groups_table(current_df, subset_columns or None)
        if groups_df.empty:
            st.info("No duplicate groups were found for the selected columns.")
        else:
            st.dataframe(groups_df, width="stretch", hide_index=True)

    with st.form("remove_duplicates_form"):
        remove_subset_columns = st.multiselect(
            "Subset columns for removal",
            current_df.columns.tolist(),
            key="remove_duplicate_subset",
            help="Leave empty to remove full-row duplicates.",
        )
        keep_strategy = st.radio("Keep which duplicate record?", options=["first", "last"], horizontal=True)
        submit_remove_duplicates = st.form_submit_button("Remove duplicates")
        if submit_remove_duplicates:
            try:
                after_df = remove_duplicates(current_df, remove_subset_columns or None, keep=keep_strategy)
                commit_change(
                    current_df,
                    after_df,
                    "remove_duplicates",
                    {"subset": remove_subset_columns, "keep": keep_strategy},
                    remove_subset_columns,
                )
            except ValueError as exc:
                st.error(str(exc))

with tab_types:
    st.write("**Current Data Types**")
    st.dataframe(
        pd.DataFrame({"column": current_df.columns, "dtype": current_df.dtypes.astype(str).values}),
        width="stretch",
        hide_index=True,
    )

    conversion_map = {
        "Convert to numeric": "numeric",
        "Convert to categorical": "categorical",
        "Convert to datetime": "datetime",
    }

    with st.form("dtype_conversion_form"):
        conversion_columns = st.multiselect("Columns to convert", current_df.columns.tolist())
        conversion_label = st.selectbox("Target type", list(conversion_map))
        remove_commas = st.checkbox("Remove commas", value=True)
        remove_currency = st.checkbox("Remove currency symbols", value=True)
        strip_spaces = st.checkbox("Strip spaces", value=True)
        date_format = st.text_input("Datetime format (optional)", help="Example: %Y-%m-%d or %d/%m/%Y")
        submit_conversion = st.form_submit_button("Apply type conversion")

        if submit_conversion:
            try:
                target_type = conversion_map[conversion_label]
                if target_type == "numeric":
                    after_df = convert_columns_to_numeric(
                        current_df,
                        conversion_columns,
                        remove_commas=remove_commas,
                        remove_currency_symbols=remove_currency,
                        strip_spaces=strip_spaces,
                    )
                elif target_type == "categorical":
                    after_df = convert_columns_to_category(current_df, conversion_columns)
                else:
                    after_df = convert_columns_to_datetime(current_df, conversion_columns, date_format or None)

                commit_change(
                    current_df,
                    after_df,
                    "convert_columns",
                    {"columns": conversion_columns, "target_type": target_type, "date_format": date_format or None},
                    conversion_columns,
                )
            except ValueError as exc:
                st.error(str(exc))

with tab_categories:
    candidate_columns = current_df.select_dtypes(include=["object", "category", "string"]).columns.tolist()
    if not candidate_columns:
        st.info("No categorical/text-like columns are available right now.")
    else:
        with st.form("categorical_cleanup_form"):
            cleanup_columns = st.multiselect("Columns for text cleanup", candidate_columns)
            cleanup_action = st.selectbox("Cleanup action", ["trim", "lower", "title"])
            submit_cleanup = st.form_submit_button("Apply categorical cleanup")
            if submit_cleanup:
                try:
                    after_df = clean_categorical_text(current_df, cleanup_columns, cleanup_action)
                    commit_change(
                        current_df,
                        after_df,
                        "clean_categorical_text",
                        {"columns": cleanup_columns, "operation": cleanup_action},
                        cleanup_columns,
                    )
                except ValueError as exc:
                    st.error(str(exc))

        mapping_column = st.selectbox("Column for mapping/replacement", candidate_columns, key="mapping_column")
        unique_values = sorted(current_df[mapping_column].dropna().astype(str).unique().tolist())
        limited_values = unique_values[:200]
        mapping_editor_df = pd.DataFrame({"current_value": limited_values, "replacement_value": [""] * len(limited_values)})
        edited_mapping_df = st.data_editor(
            mapping_editor_df,
            width="stretch",
            hide_index=True,
            key=f"mapping_editor_{mapping_column}",
        )
        if len(unique_values) > 200:
            st.caption("Only the first 200 unique values are shown in the editor to keep the page responsive.")

        if st.button("Apply mapping replacements"):
            mapping: dict[str, str] = {}
            for _, row in edited_mapping_df.iterrows():
                replacement_value = row["replacement_value"]
                if pd.notna(replacement_value) and str(replacement_value).strip():
                    mapping[str(row["current_value"])] = str(replacement_value).strip()
            try:
                after_df = apply_category_mapping(current_df, mapping_column, mapping)
                commit_change(
                    current_df,
                    after_df,
                    "apply_category_mapping",
                    {"column": mapping_column, "mapping_size": len(mapping)},
                    [mapping_column],
                )
            except ValueError as exc:
                st.error(str(exc))

        with st.form("rare_category_grouping_form"):
            rare_column = st.selectbox("Column for rare category grouping", candidate_columns, key="rare_category_column")
            rare_threshold = st.number_input("Minimum frequency to keep", min_value=1, value=10, step=1)
            other_label = st.text_input("Replacement label", value="Other")
            submit_rare_grouping = st.form_submit_button("Group rare categories")
            if submit_rare_grouping:
                try:
                    after_df = group_rare_categories(current_df, rare_column, int(rare_threshold), other_label)
                    commit_change(
                        current_df,
                        after_df,
                        "group_rare_categories",
                        {"column": rare_column, "min_frequency": int(rare_threshold), "other_label": other_label},
                        [rare_column],
                    )
                except ValueError as exc:
                    st.error(str(exc))

        with st.form("one_hot_encoding_form"):
            one_hot_columns = st.multiselect("Columns to one-hot encode", candidate_columns)
            submit_one_hot = st.form_submit_button("Apply one-hot encoding")
            if submit_one_hot:
                try:
                    after_df = one_hot_encode_columns(current_df, one_hot_columns)
                    commit_change(
                        current_df,
                        after_df,
                        "one_hot_encode_columns",
                        {"columns": one_hot_columns},
                        one_hot_columns,
                    )
                except ValueError as exc:
                    st.error(str(exc))

with tab_numeric:
    numeric_columns = current_df.select_dtypes(include=[np.number]).columns.tolist()
    selected_numeric_columns = st.multiselect(
        "Numeric columns for outlier analysis",
        numeric_columns,
        default=numeric_columns[: min(3, len(numeric_columns))],
    )

    if not selected_numeric_columns:
        st.info("Select one or more numeric columns to inspect outliers.")
    else:
        summary_col_1, summary_col_2 = st.columns(2)
        with summary_col_1:
            st.write("**IQR Outlier Summary**")
            st.dataframe(iqr_outlier_summary(current_df, selected_numeric_columns), width="stretch", hide_index=True)
        with summary_col_2:
            st.write("**Z-Score Outlier Summary**")
            st.dataframe(zscore_outlier_summary(current_df, selected_numeric_columns), width="stretch", hide_index=True)

        with st.form("numeric_outlier_action_form"):
            outlier_action = st.radio(
                "Outlier action",
                options=["do_nothing", "cap_quantiles", "remove_rows"],
                format_func=lambda value: {
                    "do_nothing": "Do nothing",
                    "cap_quantiles": "Cap / winsorize at quantiles",
                    "remove_rows": "Remove outlier rows using IQR",
                }[value],
            )
            lower_quantile = st.slider("Lower quantile", min_value=0.0, max_value=0.49, value=0.05, step=0.01)
            upper_quantile = st.slider("Upper quantile", min_value=0.51, max_value=1.0, value=0.95, step=0.01)
            iqr_multiplier = st.number_input("IQR multiplier", min_value=0.5, max_value=5.0, value=1.5, step=0.1)
            submit_outlier_action = st.form_submit_button("Apply outlier action")

            if submit_outlier_action:
                if outlier_action == "do_nothing":
                    st.info("No outlier change was applied.")
                else:
                    try:
                        before_stats = summarize_numeric_columns(current_df, selected_numeric_columns)
                        if outlier_action == "cap_quantiles":
                            after_df, capped_counts = cap_outliers_quantiles(
                                current_df,
                                selected_numeric_columns,
                                lower_quantile,
                                upper_quantile,
                            )
                            extra = {
                                "values_capped": capped_counts,
                                "before_stats": before_stats,
                                "after_stats": summarize_numeric_columns(after_df, selected_numeric_columns),
                            }
                            commit_change(
                                current_df,
                                after_df,
                                "cap_outliers_quantiles",
                                {
                                    "columns": selected_numeric_columns,
                                    "lower_quantile": lower_quantile,
                                    "upper_quantile": upper_quantile,
                                },
                                selected_numeric_columns,
                                extra=extra,
                            )
                        else:
                            after_df, removed_rows = remove_outlier_rows_iqr(
                                current_df,
                                selected_numeric_columns,
                                multiplier=float(iqr_multiplier),
                            )
                            extra = {
                                "rows_removed": removed_rows,
                                "before_stats": before_stats,
                                "after_stats": summarize_numeric_columns(after_df, selected_numeric_columns),
                            }
                            commit_change(
                                current_df,
                                after_df,
                                "remove_outlier_rows_iqr",
                                {"columns": selected_numeric_columns, "iqr_multiplier": iqr_multiplier},
                                selected_numeric_columns,
                                extra=extra,
                            )
                    except ValueError as exc:
                        st.error(str(exc))

with tab_scaling:
    scaling_columns = current_df.select_dtypes(include=[np.number]).columns.tolist()
    with st.form("scaling_form"):
        selected_scaling_columns = st.multiselect("Numeric columns to scale", scaling_columns)
        scaling_method = st.radio(
            "Scaling method",
            options=["minmax", "zscore"],
            format_func=lambda value: "Min-Max scaling" if value == "minmax" else "Z-score standardization",
            horizontal=True,
        )
        submit_scaling = st.form_submit_button("Apply scaling")
        if submit_scaling:
            try:
                before_stats = summarize_numeric_columns(current_df, selected_scaling_columns)
                after_df = scale_columns(current_df, selected_scaling_columns, scaling_method)
                extra = {
                    "before_stats": before_stats,
                    "after_stats": summarize_numeric_columns(after_df, selected_scaling_columns),
                }
                commit_change(
                    current_df,
                    after_df,
                    "scale_columns",
                    {"columns": selected_scaling_columns, "method": scaling_method},
                    selected_scaling_columns,
                    extra=extra,
                )
            except ValueError as exc:
                st.error(str(exc))

with tab_columns:
    rename_editor_df = pd.DataFrame({"current_name": current_df.columns, "new_name": current_df.columns})
    renamed_table = st.data_editor(
        rename_editor_df,
        width="stretch",
        hide_index=True,
        key="rename_editor",
    )
    if st.button("Apply column renames"):
        try:
            rename_map = {
                str(row["current_name"]): str(row["new_name"]).strip()
                for _, row in renamed_table.iterrows()
                if pd.notna(row["new_name"]) and str(row["current_name"]) != str(row["new_name"]).strip()
            }
            after_df = rename_columns(current_df, rename_map)
            commit_change(current_df, after_df, "rename_columns", {"rename_map": rename_map}, list(rename_map.values()))
        except ValueError as exc:
            st.error(str(exc))

    with st.form("drop_columns_form"):
        columns_to_drop = st.multiselect("Columns to drop", current_df.columns.tolist())
        submit_drop_columns = st.form_submit_button("Drop selected columns")
        if submit_drop_columns:
            try:
                after_df = drop_columns(current_df, columns_to_drop)
                commit_change(
                    current_df,
                    after_df,
                    "drop_columns",
                    {"columns": columns_to_drop},
                    columns_to_drop,
                )
            except ValueError as exc:
                st.error(str(exc))

    alias_map = build_column_alias_map(current_df.columns)
    with st.expander("Safe formula column aliases", expanded=False):
        alias_table = pd.DataFrame({"alias": list(alias_map.keys()), "column_name": list(alias_map.values())})
        st.dataframe(alias_table, width="stretch", hide_index=True)
        st.caption("Allowed functions: log(), sqrt(), abs(), exp(), round(), mean(), median(), min(), max(), std()")

    with st.form("formula_column_form"):
        new_column_name = st.text_input("New column name")
        formula = st.text_input("Formula", help="Example: sales_amount / units_sold or sales_amount - mean(sales_amount)")
        submit_formula = st.form_submit_button("Create formula column")
        if submit_formula:
            try:
                after_df, used_aliases = create_formula_column(current_df, new_column_name, formula, alias_map=alias_map)
                commit_change(
                    current_df,
                    after_df,
                    "create_formula_column",
                    {"new_column_name": new_column_name, "formula": formula, "alias_count": len(used_aliases)},
                    [new_column_name],
                )
            except ValueError as exc:
                st.error(str(exc))

    numeric_for_binning = current_df.select_dtypes(include=[np.number]).columns.tolist()
    with st.form("binning_form"):
        source_column = st.selectbox("Numeric column to bin", numeric_for_binning if numeric_for_binning else [""])
        binned_column_name = st.text_input("New binned column name")
        bin_method = st.radio(
            "Binning method",
            options=["equal_width", "quantile"],
            format_func=lambda value: "Equal-width bins" if value == "equal_width" else "Quantile bins",
            horizontal=True,
        )
        number_of_bins = st.number_input("Number of bins", min_value=2, max_value=20, value=4, step=1)
        submit_binning = st.form_submit_button("Create binned column")
        if submit_binning:
            try:
                after_df = bin_numeric_column(current_df, source_column, binned_column_name, bin_method, int(number_of_bins))
                commit_change(
                    current_df,
                    after_df,
                    "bin_numeric_column",
                    {
                        "source_column": source_column,
                        "new_column_name": binned_column_name,
                        "method": bin_method,
                        "bins": int(number_of_bins),
                    },
                    [source_column, binned_column_name],
                )
            except ValueError as exc:
                st.error(str(exc))

with tab_validation:
    validation_rule = st.selectbox(
        "Validation rule",
        options=["Numeric range", "Allowed categories", "Non-null constraint"],
    )

    if validation_rule == "Numeric range":
        numeric_validation_columns = current_df.select_dtypes(include=[np.number]).columns.tolist()
        selected_column = st.selectbox("Numeric column", numeric_validation_columns if numeric_validation_columns else [""])
        use_min = st.checkbox("Use minimum bound", value=True)
        min_value = st.number_input("Minimum value", value=0.0) if use_min else None
        use_max = st.checkbox("Use maximum bound", value=False)
        max_value = st.number_input("Maximum value", value=100.0) if use_max else None

        if st.button("Run numeric range validation"):
            try:
                violations_df = validate_numeric_range(current_df, selected_column, min_value, max_value)
                set_violations_df(violations_df)
                if violations_df.empty:
                    st.success("No numeric range violations were found.")
                else:
                    st.warning(f"Found {len(violations_df):,} numeric range violations.")
            except ValueError as exc:
                st.error(str(exc))

    elif validation_rule == "Allowed categories":
        category_validation_column = st.selectbox("Categorical column", current_df.columns.tolist())
        allowed_values_text = st.text_area("Allowed values (comma-separated)", help="Example: Active, Inactive, Pending")
        if st.button("Run allowed category validation"):
            try:
                allowed_values = [value.strip() for value in allowed_values_text.split(",")]
                violations_df = validate_allowed_categories(current_df, category_validation_column, allowed_values)
                set_violations_df(violations_df)
                if violations_df.empty:
                    st.success("No category violations were found.")
                else:
                    st.warning(f"Found {len(violations_df):,} category violations.")
            except ValueError as exc:
                st.error(str(exc))

    else:
        non_null_columns = st.multiselect("Columns that must not be null", current_df.columns.tolist())
        if st.button("Run non-null validation"):
            try:
                violations_df = validate_non_null(current_df, non_null_columns)
                set_violations_df(violations_df)
                if violations_df.empty:
                    st.success("No non-null violations were found.")
                else:
                    st.warning(f"Found {len(violations_df):,} non-null violations.")
            except ValueError as exc:
                st.error(str(exc))

    st.write("**Latest Violations Table**")
    latest_violations_df = st.session_state.get("violations_df")
    if isinstance(latest_violations_df, pd.DataFrame) and not latest_violations_df.empty:
        st.dataframe(latest_violations_df, width="stretch", hide_index=True)
    else:
        st.info("Run a validation rule to generate a violations table for review and export.")
