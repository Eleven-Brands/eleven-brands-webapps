"""
consolidation.py

This module combines actual past-event order data with forecasted profiles to prepare
final time-series quantities for charting and analysis.

Public API:
    build_event_sales_df(
        all_orders_df: pd.DataFrame,
        sales_regions: List[str],
        event_dates: List[datetime.date]
    ) -> pd.DataFrame:
        - Adds the target columns to the final dataframe

Internal Helpers:
    _add_forecast_cols(
        actual_df: pd.DataFrame,
        thresholds_df: pd.DataFrame
    ) -> pd.DataFrame
        - Maps dates to event days, merges average-share profiles, computes
          per-region cutoffs (T_hat), and calculates forecast quantities.
    _add_cutoff_quantities(df: pd.DataFrame) -> pd.DataFrame
        - Splits final quantities into actual vs. forecast based on cutoff thresholds,
          computes final_quantity, actual/forecast series, and cumulative metrics.
    _build_all_orders_actual_with_forecast(
        all_orders_df: pd.DataFrame,
        sales_regions: List[str],
        event_dates: List[datetime.date]
    ) -> pd.DataFrame
        - Builds a unified DataFrame containing actual and forecasted quantities,
          cumulative totals, and separate actual vs. forecast series.

Dependencies:
    - streamlit for caching decorators
    - pandas for DataFrame manipulations
    - numpy for conditional selection and arithmetic
    - config.event: EVENT_DATES, EVENT_NAME for mapping event days
    - shared.builders.forecasting.compute_hourly_share_profile for average-share
      profiles
    - shared.builders.all_orders.build_all_orders_actual_event for actual event
      thresholds
    - shared.builders.target_sales.build_target_sales_by_region_date for target sales
      for current event

Usage:
    df = _build_all_orders_actual_with_forecast(
            all_orders_df,
            SALES_REGIONS,
            EVENT_DATES
        )
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import List
import datetime

from config.event import EVENT_DATES, EVENT_NAME
from shared.builders.forecasting import compute_hourly_share_profile
from shared.builders.all_orders import build_all_orders_actual_event
from shared.builders.target_sales import build_target_sales_by_region_date


# ─── PUBLIC API ───────────────────────────────────────────────────────────────────────


@st.cache_data
def build_event_sales_df(
    all_orders_df: pd.DataFrame,
    sales_regions: List[str],
    event_dates: List[datetime.date],
) -> pd.DataFrame:
    """
    Build a consolidated event-level sales DataFrame.

    Merges actual and forecasted order quantities with target sales,
    computes cumulative share and target-based metrics, and orders
    the data by region, date, and hour for analysis and visualization.

    Parameters:
        all_orders_df: Raw orders with actual and forecast quantities.
        sales_regions: Sales region identifiers to include in the merge.
        event_dates: Ordered list of event dates for mapping.

    Returns:
        Enriched event sales data including:
            - cum_share_actual_quantity: cumulative actual / target units share
            - cum_share_forecast_quantity: cumulative forecast / target units share
            - target_quantity: per-hour target based on average share profiles
            - cum_target_quantity: cumulative target quantities by region and date
        Sorted by ['sales_region', 'local_date', 'local_hour'].
    """

    all_orders = _build_all_orders_actual_with_forecast(
        all_orders_df, sales_regions, event_dates
    )
    target_sales = build_target_sales_by_region_date()

    event_sales_df = all_orders.merge(
        right=target_sales,
        how="left",
        left_on=["sales_region", "local_date"],
        right_on=["sales_region", "event_date"],
    )

    event_sales_df["cum_share_actual_quantity"] = event_sales_df[
        "cum_actual_quantity"
    ] / event_sales_df["target_units"].replace(0, np.nan)
    event_sales_df["cum_share_forecast_quantity"] = event_sales_df[
        "cum_forecast_quantity"
    ] / event_sales_df["target_units"].replace(0, np.nan)

    event_sales_df["target_quantity"] = (
        event_sales_df["target_units"] * event_sales_df["avg_share"]
    )

    event_sales_df = event_sales_df.sort_values(
        ["sales_region", "local_date", "local_hour"]
    )

    # cumulative sum of target_quantity
    event_sales_df["cum_target_quantity"] = event_sales_df.groupby(
        ["sales_region", "local_date"]
    )["target_quantity"].cumsum()

    event_sales_df["total_share_target_quantity"] = 1

    cols = [
        "sales_region",
        "local_date",
        "local_hour",
        "actual_quantity",
        "forecast_quantity",
        "target_quantity",
        "cum_actual_quantity",
        "cum_forecast_quantity",
        "cum_target_quantity",
        "cum_share_actual_quantity",
        "cum_share_forecast_quantity",
        "total_share_target_quantity",
    ]

    return event_sales_df[cols]


# ─── BUILD DATAFRAME WITH FORECAST ────────────────────────────────────────────────────


def _add_forecast_cols(
    actual_df: pd.DataFrame,
    thresholds_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Enrich actual quantities with forecast estimates based on average-share profiles.

    This helper:
        1. Maps each local_date to its event_day index.
        2. Merges in hourly average-share profiles for the event.
        3. Computes cumulative average-share to date.
        4. Integrates cutoff thresholds (last actual date/hour) per region.
        5. Estimates total event volume (T_hat) using actual and share share.
        6. Calculates forecast_qty = avg_share * T_hat.

    Args:
        actual_df: DataFrame with actual 'quantity','sales_region','local_date',
                   'local_hour'.
        thresholds_df: DataFrame with 'sales_region','last_date','last_hour'.

    Returns:
        A dataFrame including columns:
            - sales_region, local_date, local_hour, quantity
            - event_day, avg_share, cum_avg_share
            - cutoff_date, cutoff_hour
            - T_hat, forecast_qty
    """

    event_dates = list(EVENT_DATES.values())
    # Map local_date → event_day
    date_to_day = {d: i + 1 for i, d in enumerate(event_dates)}
    actual = actual_df.copy()
    actual["event_day"] = actual["local_date"].map(date_to_day)

    # Join in the avg‐share profile
    df = actual.merge(
        compute_hourly_share_profile(EVENT_NAME),
        on=["sales_region", "event_day", "local_hour"],
        how="left",
    )

    # Compute the cumulative average‐share up to each hour
    df["cum_avg_share"] = df.groupby(["sales_region", "local_date"])[
        "avg_share"
    ].cumsum()

    # MERGE IN your per‐region cutoffs
    thr = thresholds_df.rename(
        columns={"last_date": "cutoff_date", "last_hour": "cutoff_hour"}
    )
    df = df.merge(thr, on="sales_region", how="left")

    # Extract per‐region T_hat
    cutoff = (
        df.query("local_date == cutoff_date and local_hour == cutoff_hour")
        .loc[:, ["sales_region", "local_date", "cum_quantity", "cum_avg_share"]]
        .rename(columns={"cum_quantity": "cum_actual", "cum_avg_share": "cum_share"})
    )
    cutoff["T_hat"] = cutoff["cum_actual"] / cutoff["cum_share"].replace(0, np.nan)

    # Compute forecast
    df = df.merge(
        cutoff[["sales_region", "local_date", "T_hat"]],
        on=["sales_region", "local_date"],
        how="left",
    )
    df["forecast_qty"] = df["avg_share"] * df["T_hat"]

    return df


def _add_cutoff_quantities(df: pd.DataFrame) -> pd.DataFrame:
    """
    Split final quantities into actual vs. forecast and compute cumulative metrics.

    This helper:
        - Defines masks for actual vs. forecast based on 'cutoff_date'/'cutoff_hour'.
        - Computes 'final_quantity' as actual where available, else forecast.
        - Splits 'final_quantity' into 'actual_quantity' and 'forecast_quantity'.
        - Calculates cumulative totals for each series and overall ('cum_quantity').

    Args:
        df: DataFrame with columns 'quantity', 'forecast_qty', 'sales_region',
                           'local_date', 'local_hour', 'cutoff_date', 'cutoff_hour'.

    Returns:
        A dataFrame with columns:
            - sales_region, local_date, local_hour
            - final_quantity, cum_quantity
            - actual_quantity, forecast_quantity
            - cum_actual_quantity, cum_forecast_quantity
    """

    # Build actual vs. forecast masks
    mask_actual = (df["local_date"] < df["cutoff_date"]) | (
        (df["local_date"] == df["cutoff_date"])
        & (df["local_hour"] <= df["cutoff_hour"])
    )

    mask_forecast = (df["local_date"] > df["cutoff_date"]) | (
        (df["local_date"] == df["cutoff_date"])
        & (df["local_hour"] >= df["cutoff_hour"])
    )

    # Combined final quantity
    df["final_quantity"] = np.where(
        mask_actual, df["quantity"], np.where(mask_forecast, df["forecast_qty"], np.nan)
    )

    # Split series
    df["actual_quantity"] = df["final_quantity"].where(mask_actual, np.nan)
    df["forecast_quantity"] = df["final_quantity"].where(mask_forecast, np.nan)

    # Cumulative totals
    df["cum_quantity"] = df.groupby(["sales_region", "local_date"])[
        "final_quantity"
    ].cumsum()
    df["cum_actual_quantity"] = df["cum_quantity"].where(mask_actual, np.nan)
    df["cum_forecast_quantity"] = df["cum_quantity"].where(mask_forecast, np.nan)

    cols = [
        "sales_region",
        "local_date",
        "local_hour",
        "final_quantity",
        "cum_quantity",
        "actual_quantity",
        "forecast_quantity",
        "cum_actual_quantity",
        "cum_forecast_quantity",
        "avg_share",
    ]

    return df[cols]


def _build_all_orders_actual_with_forecast(
    all_orders_df: pd.DataFrame,
    sales_regions: List[str],
    event_dates: List[datetime.date],
) -> pd.DataFrame:
    """
    Cached Function
    Build actual and forecasted order quantities for specified regions and event dates.

    This function:
        1. Retrieves actual order quantities and cutoff thresholds using
           build_all_orders_actual_event().
        2. Adds forecast columns based on average-share profiles and thresholds.
        3. Splits and computes actual vs. forecast series and cumulative metrics.

    Args:
        all_orders_df: Raw orders DataFrame with local datetime fields.
        sales_regions: List of sales region codes to include.
        event_dates: List of local dates corresponding to event days.

    Returns:
        DataFrame containing columns:
            - sales_region (str)
            - local_date (datetime.date)
            - local_hour (int)
            - final_quantity (float)
            - cum_quantity (float)
            - actual_quantity (float)
            - forecast_quantity (float)
            - cum_actual_quantity (float)
            - cum_forecast_quantity (float)
    """

    df, last_date = build_all_orders_actual_event(
        all_orders_df, sales_regions, event_dates
    )
    forecast = _add_forecast_cols(df, last_date)
    add_chart_columns = _add_cutoff_quantities(forecast)

    return add_chart_columns
