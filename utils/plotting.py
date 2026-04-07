"""Matplotlib chart builders and dataset filtering helpers."""

from __future__ import annotations

from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def filter_dataframe(
    df: pd.DataFrame,
    categorical_filters: dict[str, list[Any]] | None = None,
    numeric_filters: dict[str, tuple[float, float]] | None = None,
) -> pd.DataFrame:
    """Apply category and numeric range filters to a dataframe."""
    filtered_df = df.copy()

    for column, selected_values in (categorical_filters or {}).items():
        if column not in filtered_df.columns or not selected_values:
            continue
        normalized_values = [str(value) for value in selected_values]
        filtered_df = filtered_df[filtered_df[column].astype(str).isin(normalized_values)]

    for column, bounds in (numeric_filters or {}).items():
        if column not in filtered_df.columns or bounds is None:
            continue
        lower_bound, upper_bound = bounds
        numeric_series = pd.to_numeric(filtered_df[column], errors="coerce")
        filtered_df = filtered_df[numeric_series.between(lower_bound, upper_bound, inclusive="both")]

    return filtered_df.copy()


def _aggregate_data(
    df: pd.DataFrame,
    x_column: str,
    y_column: str | None,
    group_column: str | None,
    aggregation: str | None,
) -> pd.DataFrame:
    group_columns = [x_column] + ([group_column] if group_column else [])
    if aggregation and y_column:
        aggregated = (
            df.groupby(group_columns, dropna=False)[y_column]
            .agg(aggregation)
            .reset_index(name="value")
        )
    elif aggregation == "count" or not y_column:
        aggregated = df.groupby(group_columns, dropna=False).size().reset_index(name="value")
    else:
        aggregated = df[group_columns + [y_column]].copy().rename(columns={y_column: "value"})
    return aggregated


def create_chart(
    df: pd.DataFrame,
    chart_type: str,
    x_column: str | None = None,
    y_column: str | None = None,
    group_column: str | None = None,
    aggregation: str | None = None,
    title: str | None = None,
    x_label: str | None = None,
    y_label: str | None = None,
    rotation: int = 0,
    figsize: tuple[float, float] = (10.0, 6.0),
    bins: int = 20,
    top_n: int | None = None,
    heatmap_columns: list[str] | None = None,
) -> plt.Figure:
    """Create one of the supported matplotlib charts from a dataframe."""
    if df.empty:
        raise ValueError("No rows remain after filtering, so no chart can be drawn.")

    fig, ax = plt.subplots(figsize=figsize)
    title = title or chart_type.title()

    if chart_type == "histogram":
        if not x_column:
            raise ValueError("Select an X column for the histogram.")
        numeric_series = pd.to_numeric(df[x_column], errors="coerce").dropna()
        if numeric_series.empty:
            raise ValueError("Histogram requires a numeric X column.")

        if group_column:
            categories = df[group_column].dropna().astype(str).unique()[:8]
            for category in categories:
                subset = pd.to_numeric(df.loc[df[group_column].astype(str) == category, x_column], errors="coerce").dropna()
                if not subset.empty:
                    ax.hist(subset, bins=bins, alpha=0.55, label=str(category))
            ax.legend(title=group_column)
        else:
            ax.hist(numeric_series, bins=bins, color="#4C78A8", alpha=0.85)

        ax.set_xlabel(x_label or x_column)
        ax.set_ylabel(y_label or "Frequency")

    elif chart_type == "box":
        if not y_column:
            raise ValueError("Select a Y column for the box plot.")
        base_group = x_column or group_column
        numeric_series = pd.to_numeric(df[y_column], errors="coerce")

        if base_group:
            working_df = df[[base_group, y_column]].copy()
            working_df[y_column] = numeric_series
            working_df = working_df.dropna(subset=[base_group, y_column])
            grouped = [group[y_column].values for _, group in working_df.groupby(base_group)]
            labels = [str(label) for label, _ in working_df.groupby(base_group)]
            if not grouped:
                raise ValueError("No valid rows are available for the grouped box plot.")
            ax.boxplot(grouped, labels=labels, patch_artist=True)
            ax.set_xlabel(x_label or base_group)
        else:
            valid_values = numeric_series.dropna()
            if valid_values.empty:
                raise ValueError("Box plot requires numeric values.")
            ax.boxplot(valid_values.values, patch_artist=True)
            ax.set_xlabel(x_label or "")

        ax.set_ylabel(y_label or y_column)

    elif chart_type == "scatter":
        if not x_column or not y_column:
            raise ValueError("Select both X and Y columns for the scatter plot.")

        working_df = df[[x_column, y_column] + ([group_column] if group_column else [])].copy()
        working_df[x_column] = pd.to_numeric(working_df[x_column], errors="coerce")
        working_df[y_column] = pd.to_numeric(working_df[y_column], errors="coerce")
        working_df = working_df.dropna(subset=[x_column, y_column])
        if working_df.empty:
            raise ValueError("Scatter plot requires numeric X and Y values.")

        if group_column:
            categories = working_df[group_column].astype(str).unique()[:10]
            cmap = plt.get_cmap("tab10")
            for index, category in enumerate(categories):
                subset = working_df[working_df[group_column].astype(str) == category]
                ax.scatter(subset[x_column], subset[y_column], alpha=0.75, label=str(category), color=cmap(index))
            ax.legend(title=group_column)
        else:
            ax.scatter(working_df[x_column], working_df[y_column], alpha=0.75, color="#4C78A8")

        ax.set_xlabel(x_label or x_column)
        ax.set_ylabel(y_label or y_column)

    elif chart_type == "line":
        if not x_column or not y_column:
            raise ValueError("Select both X and Y columns for the line chart.")

        if aggregation:
            working_df = _aggregate_data(df, x_column, y_column, group_column, aggregation)
            if group_column:
                for category, group in working_df.groupby(group_column):
                    ax.plot(group[x_column], group["value"], marker="o", label=str(category))
                ax.legend(title=group_column)
            else:
                ax.plot(working_df[x_column], working_df["value"], marker="o", color="#4C78A8")
        else:
            working_df = df[[x_column, y_column] + ([group_column] if group_column else [])].copy()
            working_df[y_column] = pd.to_numeric(working_df[y_column], errors="coerce")
            working_df = working_df.dropna(subset=[x_column, y_column])
            if group_column:
                for category, group in working_df.groupby(group_column):
                    ax.plot(group[x_column], group[y_column], marker="o", label=str(category))
                ax.legend(title=group_column)
            else:
                ax.plot(working_df[x_column], working_df[y_column], marker="o", color="#4C78A8")

        ax.set_xlabel(x_label or x_column)
        ax.set_ylabel(y_label or (aggregation.title() if aggregation else y_column))

    elif chart_type == "bar":
        if not x_column:
            raise ValueError("Select an X column for the bar chart.")

        effective_aggregation = aggregation or ("count" if not y_column else "mean")
        working_df = _aggregate_data(df, x_column, y_column, group_column, effective_aggregation)
        if top_n:
            top_categories = working_df.groupby(x_column)["value"].sum().nlargest(top_n).index.tolist()
            working_df = working_df[working_df[x_column].isin(top_categories)]

        if group_column:
            pivot = working_df.pivot(index=x_column, columns=group_column, values="value").fillna(0)
            pivot.plot(kind="bar", ax=ax)
            ax.legend(title=group_column)
        else:
            ax.bar(working_df[x_column].astype(str), working_df["value"], color="#4C78A8")

        ax.set_xlabel(x_label or x_column)
        default_y = effective_aggregation.title() if effective_aggregation else ("Count" if not y_column else y_column)
        ax.set_ylabel(y_label or default_y)

    elif chart_type == "heatmap":
        numeric_columns = heatmap_columns or df.select_dtypes(include=[np.number]).columns.tolist()
        if len(numeric_columns) < 2:
            raise ValueError("Heatmap requires at least two numeric columns.")
        corr_matrix = df[numeric_columns].corr(numeric_only=True)
        image = ax.imshow(corr_matrix, cmap="coolwarm", vmin=-1, vmax=1)
        fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
        ax.set_xticks(range(len(corr_matrix.columns)))
        ax.set_yticks(range(len(corr_matrix.columns)))
        ax.set_xticklabels(corr_matrix.columns, rotation=rotation or 45, ha="right")
        ax.set_yticklabels(corr_matrix.columns)
        for row in range(len(corr_matrix.index)):
            for col in range(len(corr_matrix.columns)):
                ax.text(col, row, f"{corr_matrix.iloc[row, col]:.2f}", ha="center", va="center", color="black")
        ax.set_xlabel(x_label or "")
        ax.set_ylabel(y_label or "")

    else:
        raise ValueError("Unsupported chart type selected.")

    ax.set_title(title)
    if chart_type != "heatmap":
        plt.setp(ax.get_xticklabels(), rotation=rotation, ha="right" if rotation else "center")

    fig.tight_layout()
    return fig
