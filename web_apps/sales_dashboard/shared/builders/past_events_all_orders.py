"""
past_events_orders.py

This module provides functions for analyzing past event order data, including loading,
enriching, and aggregating orders with product model metadata.

Public API:
    get_past_events_all_order_analysis()
    get_last_event_all_order_analysis(event_name: str, last_year: int) -> pd.DataFrame

Internals:
    _get_past_events_all_orders_temp_df(): load raw past-events orders temp DataFrame
    _get_all_orders_with_product_model_df(): enrich with product model metadata

Dependencies:
    pandas
    streamlit
    shared.utils.get_temp_df
    config.config_schema.PAST_EVENTS_COLS
    shared.builders.product_model.get_product_model
"""

import pandas as pd
import streamlit as st

from shared.utils import get_temp_df
from config.config_schema import PAST_EVENTS_COLS
from shared.builders.product_model import get_product_model


# ─── PUBLIC API ───────────────────────────────────────────────────────────────


@st.cache_data
def get_past_events_all_order_analysis():
    """
    Load and aggregate past-events orders by region, event, date/time, and product.

    Retrieves the raw past-events orders DataFrame, enriches it with product model
    metadata, then groups and sums `quantity` and `item_price` by:
        - sales_region (str)
        - sales_country_code (str)
        - event_name (str)
        - local_date (datetime.date)
        - local_hour (int)
        - amazon_family (str)
        - native_family (str)
        - sku (str)

    Returns:
        Aggregated DataFrame with columns [
            'sales_region', 'sales_country_code', 'event_name',
            'local_date', 'local_hour', 'amazon_family',
            'native_family', 'sku', 'quantity', 'item_price'
        ]
    """

    df = (
        _get_all_orders_with_product_model_df()
        .groupby(
            [
                "sales_region",
                "sales_country_code",
                "local_date",
                "local_hour",
                "event_name",
                "amazon_family",
                "native_family",
                "sku",
            ],
            as_index=False,
        )
        .agg(quantity=("quantity", "sum"), item_price=("item_price", "sum"))
    )
    return df


def get_last_event_all_order_analysis(event_name: str, last_year: int):
    """
    Filter past-events order analysis for a specific event name and year.

    Args:
        event_name: Name of the event to filter.
        last_year: Year of interest (e.g., 2024).

    Returns:
        Filtered DataFrame containing orders only for the specified event and year, with
        columns including:
            - 'sales_region', 'sales_country_code', 'event_name',
            - 'local_date' (datetime.date), 'local_hour' (int),
            - 'amazon_family', 'native_family', 'sku',
            - 'quantity', 'item_price'
    """

    df = get_past_events_all_order_analysis()
    df["local_date"] = pd.to_datetime(df["local_date"])
    df = df[(df["event_name"] == event_name) & (df["local_date"].dt.year == last_year)]
    df["local_date"] = df["local_date"].dt.date

    return df


# ─── PAST EVENTS ALL ORDERS BUILDER ───────────────────────────────────────────


def _get_past_events_all_orders_temp_df() -> pd.DataFrame:
    """
    Load the raw past-events all orders temp DataFrame and reset its index.

    Returns:
         Raw DataFrame with columns defined in PAST_EVENTS_COLS,
         with a fresh integer index.
    """

    df = get_temp_df("df_all_orders_events", PAST_EVENTS_COLS)
    df = pd.DataFrame(df, copy=False).reset_index(drop=True)

    return df


def _get_all_orders_with_product_model_df() -> pd.DataFrame:
    """
    Enrich past-events orders with product model metadata and derive local order time
    components.

    Steps:
        1. Load raw past-events orders via `_get_past_events_all_orders_temp_df()`.
        2. Load the product model DataFrame via `get_product_model()`.
        3. Validate required join keys:
            - all_orders: ['sku', 'sales_country']
            - product_model: ['sku', 'sales_country_code']
        4. Perform left join on ['sku','sales_country'] -> ['sku','sales_country_code'].
        5. Drop the 'sales_country' column.
        6. Rename 'date_all_orders' to 'local_date'.
        7. Reset index to a fresh sequence.
        8. Parse 'time_all_orders' into a datetime and extract hour into 'local_hour'.

    Returns:
        Enriched DataFrame with columns:
            - local_date (datetime.date)
            - time_all_orders (str)
            - local_hour (int)
            - sales_region, sales_country_code, event_name
            - amazon_family, native_family, sku, quantity, item_price
            - product model attributes

    Raises:
         KeyError: If any required join keys are missing.
    """

    all_orders = _get_past_events_all_orders_temp_df()
    product_model = get_product_model()

    # Validate join keys
    for df, name, keys in [
        (all_orders, "all_orders", ["sku"]),
        (product_model, "product_model", ["sku", "sales_country_code"]),
    ]:
        missing = set(keys) - set(df.columns)
        if missing:
            raise KeyError(f"{name!r} missing columns: {missing}")

    merged = (
        all_orders.merge(
            product_model,
            left_on=["sku", "sales_country"],
            right_on=["sku", "sales_country_code"],
            how="left",
        )
        .drop(columns=["sales_country"])
        .rename(columns={"date_all_orders": "local_date"})
        .reset_index(drop=True)
    )

    merged["local_hour"] = pd.to_datetime(merged["time_all_orders"]).dt.hour

    return merged
