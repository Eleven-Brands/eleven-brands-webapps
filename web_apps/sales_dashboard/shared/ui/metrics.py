"""
sales_metrics.py

This module provides functions to compute and format key sales performance metrics
from order data, and to compare current-period averages against a prior period.

Public API:
    compute_metrics(all_orders_df, all_orders_df_hourly, all_orders_df_hourly_last_event)
        - Calculate total units sold and total revenue for the current event.
        - Calculate average units sold per hour and average revenue per hour.
        - Compute percentage change of current averages versus a previous event.
        - Return all values as formatted strings (with separators, currency symbols, and percent signs).

Internal Helpers:
    None
"""

import pandas as pd


# ─── PUBLIC API ──────────────────────────────────────────────────────────────


def compute_metrics(
    all_orders_df: pd.DataFrame,
    all_orders_df_hourly: pd.DataFrame,
    all_orders_df_hourly_last_event: pd.DataFrame,
) -> dict:
    """
    Compute and format sales metrics, plus percentage deltas versus a prior period.

    Calculates total and average units sold and revenue for the current dataset,
    then compares the current averages to those from a previous (last-event)
    dataset, expressing the comparison as percentage changes.

    Args:
        all_orders_df:
            Complete orders data for the current event. Must include
            columns `'quantity'` (units sold) and `'item_price'` (per-unit price).
        all_orders_df_hourly:
            Hourly-aggregated orders for the current event. Same required columns
            as `all_orders_df`.
        all_orders_df_hourly_last_event:
            Hourly-aggregated orders for the previous event. Same required columns.

    Returns:
            A dictionary mapping metric names to formatted string values:

            - **total_units_sold** (*str*): Total units sold, with thousands separator.
            - **total_revenue** (*str*): Total revenue, prefixed with `$` and two decimals.
            - **avg_units_sold** (*str*): Average units sold per hour, with thousands separator.
            - **avg_revenue** (*str*): Average revenue per hour, prefixed with `$` and two decimals.
            - **diff_units_vs_last** (*str*): Percentage change in average units sold
              versus last event, with two decimals and a `%` sign.
            - **diff_revenue_vs_last** (*str*): Percentage change in average revenue
              versus last event, with two decimals and a `%` sign.
    """

    total_units_sold = all_orders_df["quantity"].sum()
    total_revenue = all_orders_df["item_price"].sum()

    avg_units_sold = all_orders_df_hourly["quantity"].mean()
    avg_revenue = all_orders_df_hourly["item_price"].mean()

    last_avg_units = all_orders_df_hourly_last_event["quantity"].mean()
    last_avg_revenue = all_orders_df_hourly_last_event["item_price"].mean()

    diff_units = ((avg_units_sold / last_avg_units) - 1) * 100
    diff_revs = ((avg_revenue / last_avg_revenue) - 1) * 100

    return {
        "total_units_sold": f"{int(total_units_sold):,}",
        "total_revenue": f"${total_revenue:,.2f}",
        "avg_units_sold": f"{int(avg_units_sold):,}",
        "avg_revenue": f"${avg_revenue:,.2f}",
        "diff_units_vs_last": f"{diff_units:.2f}%",
        "diff_revenue_vs_last": f"{diff_revs:.2f}%",
    }
