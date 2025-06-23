"""
all_orders.py

This module provides a pipeline for loading, validating, combining, and enriching
order data from multiple marketplace regions, and for converting UTC purchase timestamps
into each order's local timezone. It exposes three public functions:

     build_all_orders_full()
     build_all_orders_region_date_hour()
     build_all_orders_actual_event()

Returns fully prepared pandas DataFrames with additional local datetime fields.

Internally, the module defines:
     - ALL_ORDER_COLS & SALES_CHANNEL: required schema and sales channel definitions imported from config.
     - _get_combined_all_orders_temp_df(): concatenate regional temp DataFrames.
     - _get_all_orders_with_product_model_df(): enrich with sales channel and product model metadata.
     - _convert_utc_to_local_timestamp(row): convert a single UTC Timestamp to local timezone.
     - _get_all_orders_with_local_datetime_df(): apply timezone conversion and extract local date/time/hour.
     - _filter_orders_by_regions_and_dates(df, regions, dates): filter orders by region and dates.
     - _aggregate_quantity_by_region_date_hour(df): aggregate quantities by region, date, and hour.
     - _fill_region_date_hour_grid(agg_df, regions, dates): fill missing region-date-hour combinations.
     - _add_daily_cumulative(df): add cumulative daily quantities.
     - _get_last_actual_thresholds_by_region(agg_df): compute last available date/hour per region.

Dependencies:
     - pandas for DataFrame operations
     - warnings & ZoneInfoNotFoundError for timezone safety
     - config.config_schema.MARKETPLACE_TZ, ALL_ORDER_COLS, SALES_CHANNEL
     - shared.utils.get_temp_df
     - shared.builders.product_model.get_product_model
"""

import streamlit as st
import pandas as pd
import warnings
from zoneinfo import ZoneInfoNotFoundError
from typing import List, Tuple
import datetime

from config.config_schema import MARKETPLACE_TZ, ALL_ORDER_COLS, SALES_CHANNEL 
from shared.utils import get_temp_df
from shared.builders.product_model import get_product_model


# ─── PUBLIC API ───────────────────────────────────────────────────────────────────────

@st.cache_data
def build_all_orders_full() -> pd.DataFrame:
     """
     Cached Function
     Load and aggregate all orders by region, date/time and product. 

     This function retrieves the all orders DataFrame with local datetime fields, then groups 
     & sums `quantity` and `item_price` by:
          - sales_region
          - sales_country_code
          - local_date
          - local_hour
          - amazon_family
          - native_family
          - sku

     Returns:
          A DataFrame with columns:
               - sales_region (str): Two-letter sales region code. 
               - sales_country_code (str): ISO country code where the order was placed. 
               - local_date (datetime.date): The date of the orders. 
               - local_hour (int): The hour of day (0-23). 
               - amazon_family (str): Amazon product grouping family classification. 
               - native_family (str): Internal immutable product family classification. 
               - sku (str): Stock-Keeping Unit identifier. 
               - quantity (int): Total quantity sold in that hour for that region. 
               - item_price (float): Total sum of item_price in that hour for that region. 
     """

     df = (
          _get_all_orders_with_local_datetime_df()
          .groupby([
               "sales_region", "sales_country_code",
               "local_date", "local_hour", 
               "amazon_family", "native_family", "sku"
          ],as_index=False)
          .agg(quantity=('quantity', 'sum'), item_price=('item_price', 'sum'))
     )
     return df


@st.cache_data
def build_all_orders_region_date_hour() -> pd.DataFrame:
     """
     Cached Function
     Load and aggregate all orders by local date, hour, and region.

     This function retrieves the all orders DataFrame with local datetime fields, then groups 
     & sums `quantity`by:
          - sales_region
          - local_date
          - local_hour

     Returns:
          A DataFrame with columns:
               - sales_region (str): Two-letter sales region code.
               - local_date (datetime.date): The date of the orders.
               - local_hour (int): The hour of day (0-23).
               - quantity (int): Total quantity sold in that hour for that region.
     """

     df = (
          _get_all_orders_with_local_datetime_df()
          .groupby(["local_date", "local_hour", "sales_region"], as_index=False)
          .agg(quantity=('quantity', 'sum'))
     )
     return df


@st.cache_data
def build_all_orders_actual_event(
    all_orders_df: pd.DataFrame,
    regions: List[str],
    event_dates: List[datetime.date]
) -> Tuple[pd.DataFrame, datetime.date]:
     """
     Cached Function
     Filter, aggregate, and prepare actual event order quantities for specified regions 
     and dates.

     This function:
          1. Filters the all_orders_df to the given regions and event dates.
          2. Aggregates hourly quantities by region, date, and hour.
          3. Fills any missing region-date-hour combinations with zero quantities.
          4. Computes daily cumulative quantities.
          5. Determines the last available date and hour thresholds for each region.

     Args:
          all_orders_df: DataFrame of all orders with local datetime fields.
          regions: List of sales region codes to include.
          event_dates: List of local dates to include.

     Returns:
          A tuple with two dataframes:
               - full_cum_df: DataFrame with columns ['sales_region', 'local_date', 
               'local_hour', 'quantity', 'cum_quantity'] covering all hours.
               - thresholds_df: DataFrame with columns ['sales_region', 'last_date', 
               'last_hour'] indicating the last available date and hour per region.
     """

     raw = _filter_orders_by_regions_and_dates(all_orders_df, regions, event_dates)
     agg = _aggregate_quantity_by_region_date_hour(raw)
     full = _fill_region_date_hour_grid(agg, regions, event_dates)
     full_cum = _add_daily_cumulative(full)
     last_date = _get_last_actual_thresholds_by_region(agg)

     return full_cum, last_date



# ─── ALL ORDERS BUILDER ───────────────────────────────────────────────────────────────

def _get_combined_all_orders_temp_df() -> pd.DataFrame:
     """
     Concatenate regional All Orders temp DataFrames into a single unified table.

     Retrieves the intermediate All Orders DataFrames for US (including CA/MX)
     and GB (including EU), concatenates them, and normalizes column names
     by replacing hyphens with underscores.

     Returns:
          A combined DataFrame containing all orders from both regions,
          with cleaned column names (e.g., "amazon-order-id" → "amazon_order_id").
     """

     us_orders = get_temp_df("df_us_all_orders_temp", ALL_ORDER_COLS)
     gb_orders = get_temp_df("df_gb_all_orders_temp",ALL_ORDER_COLS)
     combined = pd.concat([us_orders, gb_orders], ignore_index=True)
     combined.columns = combined.columns.str.replace("-", "_", regex=False)

     return combined


def _get_all_orders_with_product_model_df() -> pd.DataFrame:
     """
     Enrich the combined All Orders DataFrame with sales channel and product model 
     metadata.

     Steps:
          1. Load the concatenated All Orders temp DataFrame.
          2. Load and clean the sales_channel DataFrame.
          3. Load the product_model DataFrame.
          4. Validate required join keys in each DataFrame.
          5. Perform inner join with sales_channel on 'sales_channel'.
          6. Perform left join with product_model on ['sku', 'sales_country_code'].
          7. Reset the index.

     Returns:
          All Orders dataframe enriched with sales channel attributes and product model 
          details.

     Raises:
          KeyError: If required join key columns are missing in any DataFrame.
     """

     all_orders = _get_combined_all_orders_temp_df()
     sales_channel = get_temp_df("df_sales_channel", SALES_CHANNEL)
     product_model = get_product_model()

     # Validate join keys
     for df, name, keys in [
          (all_orders, "all_orders", ["sales_channel", "sku"]),
          (sales_channel, "sales_channel", ["sales_channel", "sales_country_code"]),
          (product_model, "product_model", ["sku", "sales_country_code"]),
     ]:
          missing = set(keys) - set(df.columns)
          if missing:
               raise KeyError(f"{name!r} missing columns: {missing}")

     merged = (
          all_orders
          .merge(sales_channel, on="sales_channel", how="inner")
          .merge(product_model, on=["sku", "sales_country_code"], how="left")
          .reset_index(drop=True)
     )

     return merged



# ─── TIMEZONE CONVERSION ──────────────────────────────────────────────────────────────

def _convert_utc_to_local_timestamp(row: pd.Series) -> pd.Timestamp:
     """
     Convert a single UTC timestamp to the marketplace's local timezone.

     Reads '__datetime_utc' and 'sales_country_code' from the row, looks up the target 
     timezone, and converts the UTC Timestamp to that local timezone. Emits a warning 
     and returns pd.NaT on failure.

     Args:
          row: Series containing:
               - '__datetime_utc': tz-aware pd.Timestamp or NaT
               - 'sales_country_code': country code for timezone lookup
               - optionally 'amazon-order-id' for warning context

     Returns:
          Converted tz-aware Timestamp, or pd.NaT if conversion fails.
     """

     tz_name = MARKETPLACE_TZ.get(row["sales_country_code"], {}).get("to_timezone")
     dt_utc = row.get("__datetime_utc")

     if not tz_name or pd.isna(dt_utc):
          return pd.NaT

     try:
          return dt_utc.tz_convert(tz_name)
     except (AttributeError, TypeError, ValueError, ZoneInfoNotFoundError) as e:
          order_id = row.get("amazon-order-id", "<unknown>")
          warnings.warn(
               f"[All Orders] could not convert UTC→{tz_name} for order {order_id}: {e}",
               stacklevel=2
          )
          return pd.NaT


def _get_all_orders_with_local_datetime_df() -> pd.DataFrame:
     """
     Return the All Orders DataFrame with local date, time, and hour columns.

     Steps:
          1. Load orders enriched with sales-channel and product-model data.
          2. Parse 'purchase_date' as UTC datetimes.
          3. Convert UTC timestamps to local timezone and strip tzinfo.
          4. Extract date, time, and hour into new columns.
          5. Insert 'local_date', 'local_time', 'local_hour' after 'purchase_date'.
          6. Drop intermediate datetime columns.

     Returns:
          All Orders dataframe with added 'local_date', 'local_time', and 'local_hour'.
     """

     df = _get_all_orders_with_product_model_df()

     df["__datetime_utc"] = pd.to_datetime(df["purchase_date"], utc=True, 
                                             errors="coerce")
     df["__datetime_local"] = df.apply(_convert_utc_to_local_timestamp, axis=1)
     df["__datetime_local"] = df["__datetime_local"].apply( 
          lambda x: x.to_pydatetime().replace(tzinfo=None) if pd.notnull(x) else None
     )

     df["__local_date"] = df["__datetime_local"].dt.date
     df["__local_time"] = df["__datetime_local"].dt.time
     df["__local_hour"] = df["__datetime_local"].dt.hour

     insert_idx = df.columns.get_loc("purchase_date") + 1
     df.insert(insert_idx, 'local_date', df["__local_date"])
     df.insert(insert_idx + 1, 'local_time', df["__local_time"])
     df.insert(insert_idx + 2, 'local_hour', df["__local_hour"])

     df.drop(columns=[
                    "__datetime_utc", "__datetime_local", "__local_date", 
                    "__local_time", "__local_hour" 
               ], inplace=True)

     return df



# ─── PREPARE MAIN DATAFRAME ───────────────────────────────────────────────────────────

def _filter_orders_by_regions_and_dates(
    df: pd.DataFrame,
    regions: List[str],
    dates: List[datetime.date]
) -> pd.DataFrame:

     """
     Filter orders to specified regions and dates.

     Args:
          df: All Orders DataFrame with columns ['sales_region', 'local_date', 'local_hour', 'quantity'].
          regions: Sales region codes to include.
          dates): Local dates to include.

     Returns:
          Filtered DataFrame with columns ['sales_region','local_date','local_hour','quantity'].
     """

     mask = (
          df['sales_region'].isin(regions) &
          df['local_date'].isin(dates)
     )

     return df.loc[mask, ['sales_region','local_date','local_hour','quantity']]



# ─── PREPARE HOURLY DATAFREAME ────────────────────────────────────────────────────────

def _aggregate_quantity_by_region_date_hour(df: pd.DataFrame) -> pd.DataFrame:
     """
     Aggregate quantity by region, date, and hour.

     Args:
          df: DataFrame with ['sales_region','local_date','local_hour','quantity'].

     Returns:
          Aggregated DataFrame with columns ['sales_region','local_date','local_hour','quantity'].
     """

     return (
          df
          .groupby(['sales_region','local_date','local_hour'], as_index=False)
          .agg(quantity=('quantity','sum'))
     )


def _fill_region_date_hour_grid(
    agg_df: pd.DataFrame,
    regions: List[str],
    dates: List[datetime.date]
) -> pd.DataFrame:
     """
     Fill missing region-date-hour combinations with zero quantity.

     Args:
          agg_df: Aggregated DataFrame with ['sales_region','local_date','local_hour','quantity'].
          regions: Sales region codes.
          dates: Local dates.

     Returns:
          DataFrame covering every region/date/hour (0-23) with missing quantities set to 0.
     """

     hours = range(24)

     full_index = pd.MultiIndex.from_product(
          [regions, dates, hours],
          names=['sales_region','local_date','local_hour']
     )

     df = (
          agg_df
          .set_index(['sales_region','local_date','local_hour'])
          .reindex(full_index, fill_value=0)
          .reset_index()
     )

     return df


def _add_daily_cumulative(df: pd.DataFrame) -> pd.DataFrame:
     """
     Add a cumulative quantity column for each region and date.

     Args:
          df: DataFrame with ['sales_region','local_date','local_hour','quantity'].

     Returns:
          DataFrame with an added 'cum_quantity' column for running daily totals.
     """

     df['cum_quantity'] = (
          df
          .groupby(['sales_region','local_date'])['quantity']
          .cumsum()
     )

     return df



# ─── GET THRESHHOLDS ──────────────────────────────────────────────────────────────────

def _get_last_actual_thresholds_by_region(agg_df: pd.DataFrame) -> pd.DataFrame:
     """
     Compute the latest available date and hour per sales region.

     Args:
          agg_df: Aggregated DataFrame with ['sales_region','local_date','local_hour',...].

     Returns:
          DataFrame with columns ['sales_region','last_date','last_hour'] indicating the 
          most recent values.
     """

     def last_for_region(df: pd.DataFrame) -> pd.Series:
          ld = df["local_date"].max()
          lh = int(df.loc[df["local_date"] == ld, "local_hour"].max())
          return pd.Series({"last_date": ld, "last_hour": lh})

     return (
          agg_df
          .groupby("sales_region", as_index=False)
          .apply(last_for_region)
          .reset_index(drop=True)
     )

