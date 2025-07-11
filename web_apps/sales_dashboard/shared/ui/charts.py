"""
charts.py

This module provides functions to render actual-vs-forecast sales charts for a given
region and date, using Altair and Streamlit.

Public API:
    hourly_chart(...) - Render an Altair chart of hourly actual-vs-forecast-vs-target
                        quantities into the provided container.
    event_chart(...) - Render an Altair chart of daily actual-vs-forecast-vs-target
                       quantities into the provided container.

Internal Helpers:
    `_df_for_plot(df, actual_col, forecast_col)`: Select and return only the
        sales_region, local_date, local_hour, actual, and forecast columns.
    `_to_long_actual_forecast(df, actual_col, forecast_col)`: Reshape a wide DataFrame
        into long form for Altair plotting (columns: local_hour, type, qty).
    `_build_altair(df_long, actual_col, forecast_col)`: Build a layered Altair line
        chart with solid line for actual data and dashed line for forecast.
"""

import streamlit as st
import pandas as pd
import datetime
import altair as alt
from streamlit.delta_generator import DeltaGenerator

from config.event import EVENT_DATES
from config.config_schema import SALES_REGIONS
from shared.builders.consolidation import build_event_sales_df


event_dates = list(EVENT_DATES.values())


# ─── PUBLIC API ──────────────────────────────────────────────────────────────


def hourly_chart(
    *,
    st_container: DeltaGenerator,
    all_orders_df: pd.DataFrame,
    date_col: str,
    sales_region_col: str,
    selected_region: str,
    selected_date: datetime.date,
    actual_col: str,
    forecast_col: str,
    target_col: str,
    is_percent: bool = False,
    has_display_labels: bool = False,
) -> None:
    """
    Render an hourly actual-vs-forecast-vs-target sales chart into the given Streamlit
    container.

    This function:
        1. Builds combined actual and forecast and target DataFrame via
           build_event_sales_df().
        2. Filters rows for the selected region and date.
        3. Transforms to long form and checks for data availability.
        4. Displays an info message if no data, else renders an Altair chart.

    Args:
        st_container: Streamlit container (e.g., st.columns(3)) for rendering.
        all_orders_df: Raw orders DataFrame with necessary fields.
        date_col: Column name for local date in all_orders_df.
        sales_region_col: Column name for sales region in all_orders_df.
        selected_region: The region code to filter data.
        selected_date: The date to filter data.
        actual_col: Column name for actual quantity.
        forecast_col: Column name for forecast quantity.
        target_col: Column name for target quantity.
        is_percent: Boolean for formatting as percentage.
        has_display_labels: Boolean whether to display labels in charts.

    Returns:
        None. Renders chart or info message in the provided container.
    """

    new_build = build_event_sales_df(all_orders_df, SALES_REGIONS, event_dates)
    new_build = new_build[
        (new_build[sales_region_col] == selected_region)
        & (new_build[date_col] == selected_date)
    ]

    df_long = _to_long_actual_forecast(new_build, actual_col, forecast_col, target_col)

    all_none = df_long["qty"].isna().all()

    if all_none:
        st_container.info("No sales data for this region on the selected date.")
        return

    st_container.altair_chart(
        _build_altair(
            df_long,
            actual_col,
            forecast_col,
            target_col,
            is_percent,
            has_display_labels,
        ),
        use_container_width=True,
    )

    return


def event_chart(
    *,
    st_container: DeltaGenerator,
    all_orders_df: pd.DataFrame,
    date_col: str,
    sales_region_col: str,
    selected_region: str,
    actual_col: str,
    forecast_col: str,
    target_col: str,
) -> None:
    """
    Render an daily actual-vs-forecast-vs-target sales chart into the given Streamlit
    container.

    This function:
        1. Builds combined actual and forecast and target DataFrame via
           build_event_sales_df().
        2. Filters rows for the selected region.
        3. Transforms to long form and checks for data availability.

    Args:
        st_container: Streamlit container (e.g., st.columns(3)) for rendering.
        all_orders_df: Raw orders DataFrame with necessary fields.
        date_col: Column name for local date in all_orders_df.
        sales_region_col: Column name for sales region in all_orders_df.
        selected_region: The region code to filter data.
        selected_date: The date to filter data.
        actual_col: Column name for actual quantity.
        forecast_col: Column name for forecast quantity.
        target_col: Column name for target quantity.
        is_percent: Boolean for formatting as percentage.
        has_display_labels: Boolean whether to display labels in charts.

    Returns:
        None. Renders chart in the provided container.
    """

    new_build = build_event_sales_df(all_orders_df, SALES_REGIONS, event_dates)
    new_build = new_build[(new_build[sales_region_col] == selected_region)]

    df_grouped = new_build.groupby([date_col], as_index=False).agg(
        actual=(actual_col, "sum"),
        forecast=(forecast_col, "sum"),
        target=(target_col, "sum"),
    )

    df_grouped[date_col] = pd.to_datetime(df_grouped[date_col])
    df_grouped["date_label"] = df_grouped[date_col].dt.strftime("%b %d")

    # Define Chart Axis
    x = alt.X(
        "date_label:O",
        title="Date",
        sort=alt.EncodingSortField(field=date_col),
        axis=alt.Axis(labelAngle=0, labelAlign="center"),
    )

    # Define Chart Series
    # Forecast
    forecast_bars = (
        alt.Chart(df_grouped)
        .mark_bar(
            cornerRadiusTopLeft=5,
            cornerRadiusTopRight=5,
            opacity=0.7,
            size=40,
            color="#ea4335",
        )
        .encode(
            x=x,
            y=alt.Y(
                "forecast:Q",
                title="Units Sold",
            ),
            tooltip=[
                date_col,
                alt.Tooltip("forecast:Q", title="Forecast", format=".1f"),
            ],
        )
    )

    # Actual
    actual_bars = (
        alt.Chart(df_grouped)
        .mark_bar(
            cornerRadiusTopLeft=5, cornerRadiusTopRight=5, size=20, color="#98b9d0"
        )
        .encode(
            x=x,
            y=alt.Y("actual:Q"),
            tooltip=[date_col, alt.Tooltip("actual:Q", title="Actual", format=".0f")],
        )
    )

    # Target
    target_bars = (
        alt.Chart(df_grouped)
        .mark_bar(
            cornerRadiusTopLeft=5,
            cornerRadiusTopRight=5,
            opacity=0.3,
            size=60,
            color="#d89663",
        )
        .encode(
            x=x,
            y=alt.Y("target:Q", title="Units Sold"),
            tooltip=[date_col, alt.Tooltip("target:Q", title="Target", format=".1f")],
        )
    )

    # Make chart
    chart = (target_bars + forecast_bars + actual_bars).properties(
        width="container",
        height=300,
        title="Actual vs Forecast vs Target (in order thinner to thicker)",
    )

    # Render Chart
    st_container.altair_chart(chart, use_container_width=True)


# ─── BUILD DATAFRAMES ────────────────────────────────────────────────────────


def _df_for_plot(df, actual_col, forecast_col, target_col):
    """
    Select relevant columns for plotting: region, date, hour, actual and forecast.

    Args:
         df: DataFrame containing full dataset.
         actual_col: Column name for actual quantity.
         forecast_col: Column name for forecast quantity.
         target_col: Column name for target quantity.

    Returns:
         Subset with ['sales_region','local_date','local_hour',actual_col,forecast_col].
    """

    return df[
        ["sales_region", "local_date", "local_hour"]
        + [actual_col, forecast_col, target_col]
    ]


# ─── ALTAIR CHART ────────────────────────────────────────────────────────────


@st.cache_data
def _to_long_actual_forecast(
    df: pd.DataFrame, actual_col: str, forecast_col: str, target_col: str
) -> pd.DataFrame:
    """
    Reshape actual and forecast columns into long form for Altair plotting.

    This function melts the DataFrame on 'local_hour', converting wide columns
    [actual_col, forecast_col] into rows with 'type' and 'qty' columns.

    Args:
         df: DataFrame with columns: 'local_hour', actual_col, forecast_col.
         actual_col: Column name for actual quantity.
         forecast_col: Column name for forecast quantity.
         target_col: Column name for target quantity.

    Returns:
         Long-form DataFrame with columns ['local_hour', 'type', 'qty'].
    """

    df_plot = _df_for_plot(df, actual_col, forecast_col, target_col)
    df_long = df_plot.melt(
        id_vars="local_hour",
        value_vars=[actual_col, forecast_col, target_col],
        var_name="type",
        value_name="qty",
    )

    return df_long


def _build_altair(
    df_long: pd.DataFrame,
    actual_col,
    forecast_col,
    target_col,
    is_percent,
    has_display_labels,
    actual_label: str = "Actual",
    forecast_label: str = "Forecast",
    target_label: str = "Target",
) -> alt.Chart:
    """
    Construct a layered Altair line chart for actual vs. forecast quantities.

    This function:
         - Renames 'type' values to provided labels.
         - Encodes 'local_hour' on x-axis and 'qty' on y-axis.
         - Uses solid line for actual data and dashed line for forecast.
         - Applies distinct stroke widths and color ordering.

    Args:
         df_long: Long-form DataFrame with columns ['local_hour', 'type', 'qty'].
         actual_col: Original column name for actual quantity (used for label mapping).
         forecast_col: Original column name for forecast quantity.
         actual_label: Label for actual series in legend.
         forecast_label: Label for forecast series in legend.
         target_label: Label for target series in legend.

    Returns:
         Configured Altair Chart object ready for rendering.
    """

    df = df_long.copy()
    df["type"] = df["type"].replace(
        {
            actual_col: actual_label,
            forecast_col: forecast_label,
            target_col: target_label,
        }
    )

    y_max = df["qty"].max() * 1.2

    axis_fmt = ".0%" if is_percent else ".1f"
    text_fmt = ".0%" if is_percent else ".2f"

    base = alt.Chart(df).encode(
        x=alt.X(
            "local_hour:Q",
            title="Hour of Day",
            scale=alt.Scale(domain=[0, 23], nice=False),
            axis=alt.Axis(tickMinStep=1, tickCount=24),
        ),
        y=alt.Y(
            "qty:Q",
            title="Quantity" if not is_percent else "Percentage",
            scale=alt.Scale(domain=[0, y_max], nice=True),
            axis=alt.Axis(format=axis_fmt),
        ),
        color=alt.Color(
            "type:N",
            title="Series",
            scale=alt.Scale(
                domain=[actual_label, forecast_label, target_label],
                range=["#98b9d0", "#ea4335", "#d89663"],
            ),
            sort=[actual_label, forecast_label, target_label],
        ),
    )

    actual_line = (
        base.mark_line()
        .encode(strokeWidth=alt.value(4))
        .transform_filter(alt.datum.type == actual_label)
    )

    forecast_line = (
        base.mark_line()
        .encode(strokeDash=alt.value([5, 5]), strokeWidth=alt.value(4))
        .transform_filter(alt.datum.type == forecast_label)
    )

    target_line = (
        base.mark_line()
        .encode(strokeWidth=alt.value(4))
        .transform_filter(alt.datum.type == target_label)
    )

    lines = actual_line + forecast_line + target_line

    # Point & Labels
    two_series = (alt.datum.type == actual_label) | (alt.datum.type == forecast_label)

    points = base.mark_point(size=60, opacity=0.7).transform_filter(two_series)

    labels_above = (
        base.mark_text(dy=-25, fontSize=15)
        .transform_filter(two_series & ((alt.datum.local_hour % 2) == 0))
        .encode(text=alt.Text("qty:Q", format=text_fmt))
    )

    labels_below = (
        base.mark_text(dy=25, fontSize=15)
        .transform_filter(two_series & ((alt.datum.local_hour % 2) == 1))
        .encode(text=alt.Text("qty:Q", format=text_fmt))
    )

    points_and_labels = points + labels_above + labels_below

    if has_display_labels:
        return lines + points_and_labels
    else:
        return lines
