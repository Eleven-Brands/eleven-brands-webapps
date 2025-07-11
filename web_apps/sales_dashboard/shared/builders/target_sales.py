"""
target_sales.py

This module loads, enriches, and aggregates Primeday 2025 target sales data,
producing summaries of target revenue and units for analysis and reporting.

Public API:
    build_target_sales_by_region_date() -> pandas.DataFrame
        - Aggregates target revenue and units by sales_region, event_date, and day.
    build_target_sales_by_region_sku_date() -> pandas.DataFrame
        - Aggregates target revenue and units by sales_region, sku, amazon_family, event_date, and day.

Internal Helpers:
    _get_target_sales_df() -> pandas.DataFrame
        - Loads raw target sales data for each event day using configured schema.
    _get_target_sales_with_dates() -> pandas.DataFrame
        - Maps day indices to actual event dates, adding an `event_date` column.

Dependencies:
    - pandas for DataFrame operations
    - shared.utils.get_temp_df for loading temporary tables
    - config.config_schema.TARGET_COLS for selecting target columns
    - config.event.EVENT_DATES for mapping event days to dates

Usage:
    df = build_target_sales_by_region_date()
"""

from shared.utils import get_temp_df
from shared.builders.product_model import get_product_model
from config.config_schema import TARGET_COLS
from config.event import EVENT_DATES

event_dates = list(EVENT_DATES.values())


# ─── PUBLIC API ───────────────────────────────────────────────────────────────────────


def build_target_sales_by_region_date():
    """
    Aggregate target sales by sales region, event date, and day index.

    Groups the enriched target DataFrame on 'sales_region', 'event_date',
    and 'day', summing up revenue and units sold targets for each grouping.

    Returns:
        MultiIndexed by ['sales_region', 'event_date', 'day'], containing
        'target_revenue' and 'target_units' as summed values.
    """

    target_df = _get_target_sales_with_dates()
    aggregate = target_df.groupby(["sales_region", "event_date", "day"]).agg(
        target_revenue=("revenue", "sum"), target_units=("units", "sum")
    )

    return aggregate


def build_target_sales_by_region_sku_date():
    """
    Aggregate target sales by sales region, amazon_family, sku, event date, and day index.

    Returns:
        MultiIndexed by ['sales_region', 'amazon_family', 'sku', 'event_date', 'day'], containing
        'target_revenue' and 'target_units' as summed values.
    """

    target_df = _get_target_sales_with_dates()
    aggregate = target_df.groupby(
        ["sales_region", "sku", "amazon_family", "event_date", "day"]
    ).agg(target_revenue=("revenue", "sum"), target_units=("units", "sum"))

    return aggregate


# ─── BUILD TARGET SALES DATAFRAME ─────────────────────────────────────────────────────


def _get_target_sales_df():
    """
    Retrieve the raw target sales DataFrame for Primeday 2025.

    Uses a temporary table name and the configured target columns to
    load the target revenue and unit data for each day of the event.

    Returns:
        Raw target sales data with columns defined in TARGET_COLS.
    """

    return get_temp_df("target_primeday_2025_06", TARGET_COLS)


def _get_target_sales_with_dates():
    """
    Enrich raw target sales with event dates and product-region metadata.

    Returns:
        pd.DataFrame: target sales with columns
            ['sku', 'amazon_family', 'sales_region', 'day',
             'event_date', 'target_units', 'target_revenue'].
    """

    product_model = get_product_model()[["sku", "amazon_family", "sales_country_code"]]
    product_model["sales_country_code"] = product_model["sales_country_code"].replace(
        "DE", "EU"
    )
    product_model = product_model[
        product_model["sales_country_code"].isin(["US", "CA", "GB", "EU"])
    ]
    product_model.rename(columns={"sales_country_code": "sales_region"}, inplace=True)

    target_df = _get_target_sales_df()
    target_df["event_date"] = target_df["day"].apply(lambda d: event_dates[d - 1])

    merged = target_df.merge(
        product_model, on=["sku", "sales_region"], how="left"
    ).reset_index(drop=True)

    return merged
