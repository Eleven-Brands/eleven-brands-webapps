"""
matrices.py

This module provides functions to build DataFrames that combine actual and target
sales by region, family, and SKU, and to calculate progress metrics for use in
Streamlit dashboards.

Public API:
    build_st_dataframe(all_orders_df_analysis) -> pd.DataFrame
        - Merge actual and target sales, then compute percentage progress for
          units sold and revenue against targets.

Internal Helpers:
    _build_event_sales_df(actual_sales, target_sales) -> pd.DataFrame
        - Aggregate actual sales by sales_region, amazon_family, and SKU
          (units_sold and revenue), then merge with the target sales DataFrame.
"""

from shared.builders.target_sales import build_target_sales_by_region_sku_date
from shared.builders.committed_units import build_committed_units_by_region_sku_date
import numpy as np
import pandas as pd



# ─── PUBLIC API ──────────────────────────────────────────────────────────────

def build_st_dataframe(
     all_orders_df_analysis: pd.DataFrame,
     group_by_cols: list
):
     """
     Build a DataFrame for Streamlit that includes actual vs. target progress metrics.

     Retrieves target sales by region, SKU, and date, merges with actual sales,
     and calculates progress percentages for units sold and revenue.

     Args:
          all_orders_df_analysis:
               Raw orders data for the current event. Must include 'sales_region',
               'amazon_family', 'sku', 'quantity', and 'item_price'.

     Returns:
          A DataFrame with columns:
               - sales_region
               - amazon_family
               - sku
               - units_sold
               - revenue
               - target_units
               - target_revenue
               - progress_units_sold (float, % of target_units)
               - progress_revenue (float, % of target_revenue)
     """

     target_sales = build_target_sales_by_region_sku_date()
     committed = build_committed_units_by_region_sku_date()
     event_sales = _build_event_sales_df(all_orders_df_analysis, target_sales, committed, group_by_cols)

     # Calculate Differences
     event_sales["units_diff"] = event_sales["units_sold"] - event_sales["target_units"]
     event_sales["committed_diff"] = event_sales["units_sold"] - event_sales["committed_units"]
     event_sales["revenue_diff"] = event_sales["revenue"] - event_sales["target_revenue"]

     # Calculate Progress
     event_sales["progress_units_sold"] = np.where(
          event_sales["target_units"] > 0,
          event_sales["units_sold"]  / event_sales["target_units"]  * 100,
          0.0
     )

     event_sales["progress_committed"] = np.where(
          event_sales["committed_units"] > 0,
          event_sales["units_sold"]  / event_sales["committed_units"]  * 100,
          0.0
     )

     event_sales["progress_revenue"] = np.where(
          event_sales["target_revenue"] > 0,
          event_sales["revenue"]     / event_sales["target_revenue"] * 100,
          0.0
     )

     return event_sales



# ─── BUILD DATAFRAMES ────────────────────────────────────────────────────────

def _build_event_sales_df(
        actual_sales: pd.DataFrame,
        target_sales: pd.DataFrame,
        committed_units: pd.DataFrame,
        group_by_cols: list
) -> pd.DataFrame:
     """
     Aggregate actual sales and merge with target sales.

     Groups actual sales by sales_region, amazon_family, and SKU to compute
     total units_sold and revenue, then merges with the target_sales DataFrame
     on sales_region and SKU.

     Args:
          actual_sales:
               Raw orders data with 'sales_region', 'amazon_family', 'sku',
               'quantity', and 'item_price'.
          target_sales:
               Target sales data with 'sales_region', 'sku',
               'target_units', and 'target_revenue'.

     Returns:
          A merged DataFrame containing:
               - sales_region
               - amazon_family
               - sku
               - units_sold
               - revenue
               - target_units
               - target_revenue
     """

     skus_actual = actual_sales.reset_index()
     skus_actual.rename(columns={"local_date": "event_date"}, inplace=True)
     skus_actual = skus_actual[group_by_cols]

     skus_target = target_sales.reset_index()
     skus_target = skus_target[group_by_cols]

     skus_combined = (
          pd.concat([skus_actual, skus_target], ignore_index=True)
          .drop_duplicates()
          .reset_index(drop=True)
     )


     actual_sales.rename(columns={"local_date": "event_date"}, inplace=True)

     actual = (
          actual_sales
          .groupby(group_by_cols)
          .agg(units_sold=("quantity", "sum"), revenue=("item_price", "sum"))
          .reset_index()
     )

     target = (
          target_sales
          .groupby(group_by_cols)
          .agg(target_units=("target_units", "sum"), target_revenue=("target_revenue", "sum"))
          .reset_index()
     )

     committed = (
          committed_units
          .groupby(group_by_cols)
          .agg(committed_units=("committed_units", "sum"))
          .reset_index()
     )

     merged = (
          skus_combined
          .merge(actual, on=group_by_cols, how="left")
          .merge(target, on=group_by_cols, how="left")
          .merge(committed, on=group_by_cols, how="left")
          .fillna(0)
     )

     return merged



