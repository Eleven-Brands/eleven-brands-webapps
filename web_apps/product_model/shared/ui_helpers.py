"""
ui_helper.py

This module provides helper functions for building Streamlit UI components, including:
- Constructing column configuration from schema metadata
- Combining column aliases across multiple schema definitions
- Filtering DataFrames by column values and complex criteria
"""

import streamlit as st
import pandas as pd


def build_column_config_from_schema(
          df: pd.DataFrame, 
          schema: dict
     ) -> dict:
     """
     Build a Streamlit column_config dictionary based on schema metadata.

     Args:
          df (pd.DataFrame): The DataFrame whose columns will be configured.
          schema (dict): A mapping of column names to metadata dicts. Metadata keys:
               - alias (str): Display label for the column.
               - help (str): Help text for the column.
               - type (str): Data type, one of "STRING", "FLOAT", or "INTEGER".

     Returns:
          dict: A mapping of column names to Streamlit column_config objects
               (TextColumn or NumberColumn) with label, help, format, pinned, and width.
     """

     config = {}
     for col in df.columns:
          meta = schema.get(col, {})
          label = meta.get("alias", col)
          help_text = meta.get("help", "")
          col_type = meta.get("type", "STRING")
          pinned = col in ["base_sku", "sku"]

          width = 150
          if col in ["base_sku", "sku"]:
               width = 170
          elif col_type == "FLOAT":
               width = 150
          elif col_type == "INTEGER":
               width = 120
          elif len(label) > 20:
               width = 200

          if col_type == "FLOAT":
               config[col] = st.column_config.NumberColumn(label=label, help=help_text, format="%.2f", pinned=pinned, width=width)
          elif col_type == "INTEGER":
               config[col] = st.column_config.NumberColumn(label=label, help=help_text, format="%d", pinned=pinned, width=width)
          else:
               config[col] = st.column_config.TextColumn(label=label, help=help_text, pinned=pinned, width=width)
     return config


def combined_aliases(
          df: pd.DataFrame, 
          *schemas: dict
     ) -> pd.DataFrame:
     """
     Rename DataFrame columns by combining "alias" entries from multiple schemas.

     Args:
          df (pd.DataFrame): The DataFrame whose columns will be renamed.
          *schemas (dict): One or more schema dicts mapping column names to metadata
               dicts that may contain an "alias" key.

     Returns:
          pd.DataFrame: A new DataFrame with columns renamed to their alias values
               if provided; otherwise, original column names are retained.
     """

     all_aliases = {}
     for schema in schemas:
          all_aliases.update({
               col: props.get("alias", col)
               for col, props in schema.items()
               if props.get("alias")
          })
     return df.rename(columns=all_aliases)


def filter_by_column(
          df: pd.DataFrame, 
          column: str, 
          query: str
     ) -> pd.DataFrame:
     """
     Create a boolean mask for rows where a column contains a query string.

     Args:
          df (pd.DataFrame): The DataFrame to filter.
          column (str): Name of the column to search within.
          query (str): Substring to match (case-insensitive).

     Returns:
          pd.Series: A boolean Series indicating which rows contain the query;
               returns all False if column not in df.
     """

     if column in df.columns:
          return df[column].astype(str).str.contains(query, case=False, na=False)

     return pd.Series(False, index=df.index)

def apply_filters(
          df: pd.DataFrame,
          base_sku: str = None,
          native_families: list[str] = None,
          countries: list[str] = None,
          suppliers: list[str] = None
     ) -> pd.DataFrame:
     """
     Apply multiple filters to a DataFrame based on supplier, country, family, and SKU.

     Args:
          df (pd.DataFrame): The DataFrame to filter.
          base_sku (str, optional): Substring filter for SKU or base_sku columns.
          native_families (list[str], optional): Filter to include only these native families;
               ignored if None or ['All'].
          countries (list[str], optional): Filter to include only these country codes;
               ignored if None or ['All'].
          suppliers (list[str], optional): Filter to include only these suppliers;
               ignored if None or ['All'].

     Returns:
          pd.DataFrame: The filtered DataFrame.
     """

     if "supplier" in df.columns and suppliers and suppliers != ['All']:
          df = df[df["supplier"].isin(suppliers)]

     if "sales_country_code" in df.columns and countries and countries != ['All']:
          df = df[df["sales_country_code"].isin(countries)]

     if "native_family" in df.columns and native_families and native_families != ['All']:
          df = df[df["native_family"].isin(native_families)]

     if base_sku:
          mask = (
               filter_by_column(df, "sku", base_sku) |
               filter_by_column(df, "base_sku", base_sku)
          )
          df = df[mask]

     return df
