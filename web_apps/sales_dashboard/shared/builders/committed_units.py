"""
committed_units.py

This module loads, enriches, and aggregates Primeday 2025 committed units data,
producing summaries of commited_units for analysis and reporting.

Public API:
    build_committed_units_by_region_sku_date() -> pandas.DataFrame
        - Aggregates committed_units by sales_region, sku, amazon_family and event_date.

Internal Helpers:
    _get_committed_units_df() -> pandas.DataFrame
        - Loads raw committed units data for each event day using configured schema.
    _get_committed_units_with_product_model() -> pandas.DataFrame
        - Adds `amazon _family` column.

Dependencies:
    - pandas for DataFrame operations
    - shared.utils.get_temp_df for loading temporary tables
    - config.config_schema.COMMIT_COLS for selecting target columns

Usage:
    df = build_committed_units_by_region_sku_date()
"""


import pandas as pd
from shared.utils import get_temp_df
from shared.builders.product_model import get_product_model
from config.config_schema import COMMIT_COLS



# ─── PUBLIC API ───────────────────────────────────────────────────────────────────────

def build_committed_units_by_region_sku_date():
    """
    Aggregate committed units by sales region, amazon_family, sku, event date.

    Returns:
        MultiIndexed by ['sales_region', 'amazon_family', 'sku', 'event_date'], containing 
        'committed_units' as summed values.
    """

    target_df = _get_committed_units_with_product_model()
    target_df["event_date"] = pd.to_datetime(target_df["event_date"]).dt.date
    aggregate = (
        target_df
        .groupby(["sales_region", "sku", "amazon_family", "event_date"])
        .agg(committed_units=("committed_units", "sum"))
    )

    return aggregate



# ─── BUILD COMMITED UNITS DATAFRAME ───────────────────────────────────────────────────

def _get_committed_units_df():
    """
    Retrieve the raw committed units DataFrame for Primeday 2025.

    Uses a temporary table name and the configured target columns to
    load the target revenue and unit data for each day of the event.

    Returns:
        Raw committed units data with columns defined in COMMIT_COLS.
    """

    return get_temp_df("committed_units_2025_06", COMMIT_COLS)


def _get_committed_units_with_product_model():
    """
    Enrich raw committed units with event dates and product-region metadata.

    Returns:
        pd.DataFrame: committed units with columns 
            ['sku', 'amazon_family', 'sales_region', 
             'event_date', 'committed_units'].
    """

    product_model = get_product_model()[["sku", "amazon_family", "sales_country_code"]]
    product_model["sales_country_code"] = product_model["sales_country_code"].replace("DE", "EU")
    product_model = product_model[product_model["sales_country_code"].isin(["US", "CA", "GB", "EU"])]
    product_model.rename(columns={"sales_country_code": "sales_region"}, inplace=True)


    target_df = _get_committed_units_df()

    merged = (
        target_df
        .merge(product_model, on=["sku", "sales_region"], how="left")
        .reset_index(drop=True)
    )

    return merged
