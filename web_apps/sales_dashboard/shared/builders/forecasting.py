"""
forecasting.py

This module provides utilities to load past hourly sales data for specific events,
compute normalized hourly share profiles, and generate combined actual-versus-forecast
sales profiles by hour for a given region, event-day, and date. It is optimized for use
in a Streamlit app with caching applied to the main public interface.

Public API:
    build_region_forecast
    last_hour_by_region

Internal Helpers (prefixed with `_`):
    _get_past_hourly_sales_for_event
    _compute_hourly_share_profile

Constants:
    AVERAGE_MAPPING: mapping of historical event days to forecast days
    MAPPING_DF: lookup DataFrame built from AVERAGE_MAPPING
"""

import pandas as pd
import streamlit as st

from shared.utils import get_temp_df
from config.config_schema import PAST_EVENTS_COLS

AVERAGE_MAPPING = {1: [1, 2], 2: [1, 2], 3: [1, 2], 4: [1, 2]}

MAPPING_DF = pd.DataFrame(
    [
        {"new_event_day": new_day, "mapped_day": old_day}
        for new_day, old_days in AVERAGE_MAPPING.items()
        for old_day in old_days
    ]
)


# ─── PUBLIC API ───────────────────────────────────────────────────────────────


@st.cache_data
def compute_hourly_share_profile(event_name: str) -> pd.DataFrame:
    """
    Build a normalized hourly share profile for a given event across regions.

    This internal helper fetches past hourly sales for the specified event, pivots it
    into a 24-hour matrix by (event_date, sales_region, event_day), converts volumes
    into per-hour share vectors, and then averages those shares across historical days
    according to AVERAGE_MAPPING. The result is a DataFrame of mean share by
    (sales_region, event_day, local_hour).

    Args:
        event_name: Name of the event to process (e.g. "Prime Day").

    Returns:
        A DataFrame sorted by ['sales_region', 'event_day', 'local_hour']
        with columns:
            - sales_region: region code
            - event_day: mapped event day for forecasting
            - local_hour: hour of day (0-23)
            - avg_share: mean share of hourly volume for that region/day

    Notes:
        - Internally calls `_get_past_hourly_sales_for_event` to load and
          aggregate quantities.
        - Uses the global `MAPPING_DF` (built from AVERAGE_MAPPING) to map
          historical event days onto the final “forecast” event_day values.
        - Rows with zero total volume will produce zero share for all hours.
    """

    past_event_df = _get_past_hourly_sales_for_event(event_name)

    # Pivot & fill zeros exactly as you have it
    hourly_matrix = past_event_df.pivot_table(
        index=["event_date", "sales_region", "event_day"],
        columns="local_hour",
        values="hourly_qty",
        aggfunc="sum",
        fill_value=0,
    ).reindex(columns=range(24), fill_value=0)

    # Compute each event’s share‐vector
    wide_shares = hourly_matrix.div(hourly_matrix.sum(axis=1), axis=0)

    # Melt back to long form
    long_shares = (
        wide_shares.reset_index()
        .melt(
            id_vars=["event_date", "sales_region", "event_day"],
            var_name="local_hour",
            value_name="share",
        )
        .assign(local_hour=lambda df: df["local_hour"].astype(int))
    )

    # Build the base profile (mean share by region/day/hour)
    base_profile = long_shares.groupby(
        ["sales_region", "event_day", "local_hour"], as_index=False
    ).agg(avg_share=("share", "mean"))

    # Merge & Re-aggregate & Sort
    profile = (
        base_profile.merge(
            MAPPING_DF, left_on="event_day", right_on="mapped_day", how="right"
        )
        .groupby(["sales_region", "new_event_day", "local_hour"], as_index=False)
        .agg(avg_share=("avg_share", "mean"))
        .rename(columns={"new_event_day": "event_day"})
        .sort_values(["sales_region", "event_day", "local_hour"])
    )

    return profile


# ─── PAST SALES ───────────────────────────────────────────────────────────────


def _get_past_hourly_sales_for_event(event_name: str) -> pd.DataFrame:
    """
    Load and aggregate historical order quantities by hour for a given event.

    This internal helper pulls the raw “All Orders Events” DataFrame from session
    storage, filters it to only the specified event, parses timestamps to extract
    the local hour, and then computes total quantity sold in each hour, for each
    event date and sales region.

    Args:
         event_name:
              Name of the event to filter on (e.g. "Prime Day").

    Returns:
         pd.DataFrame:
              A DataFrame with one row per combination of
              (event_date, local_hour, sales_region, event_name, event_day) and columns:
              - event_date: date of the event occurrence
              - local_hour: hour of day (0-23) when the order occurred
              - sales_region: region code for the sale
              - event_name: the same event_name you passed in
              - event_day: ordinal day of the event (1, 2, …)
              - hourly_qty: total quantity sold in that hour

    Notes:
         - Rows with unparsable timestamps are dropped.
         - If no records are found for `event_name`, an empty DataFrame is returned
              (after emitting a Streamlit warning).
    """

    # Load & filter
    df = (
        get_temp_df("df_all_orders_events", PAST_EVENTS_COLS)
        .query("event_name == @event_name")
        .assign(
            time_all_orders=lambda df: pd.to_datetime(
                df["time_all_orders"].astype(str), format="%H:%M:%S", errors="coerce"
            ),
            local_hour=lambda df: df["time_all_orders"].dt.hour,
        )
        .dropna(subset=["local_hour"])
        .groupby(
            ["event_date", "local_hour", "sales_region", "event_name", "event_day"],
            as_index=False,
        )
        .agg(hourly_qty=("quantity", "sum"))
    )

    if df.empty:
        st.warning(f"No sales found for event {event_name!r}")

    result = df.sort_values(["event_date", "local_hour"])

    return result
