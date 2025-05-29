"""
dataframe_builder.py

This module provides functions to build and merge Pandas DataFrames for 
product catalogs, including caching and column reordering utilities.
"""

import pandas as pd
import streamlit as st


def reorder_after(
          df: pd.DataFrame, 
          anchor: str, 
          to_insert: list[str]
     ) -> pd.DataFrame:

     """
     Reorder columns in a DataFrame by inserting specified columns immediately after an anchor column.

     Args:
          df (pd.DataFrame): The input DataFrame whose columns are to be reordered.
          anchor (str): The column name after which the new columns should be inserted.
          to_insert (list[str]): A list of column names to insert after the anchor column.

     Returns:
          pd.DataFrame: A new DataFrame with columns reordered.
     """

     cols = [c for c in df.columns if c not in to_insert]
     if anchor in cols:
          idx = cols.index(anchor) + 1
          for i, c in enumerate(to_insert):
               cols.insert(idx + i, c)
     return df[cols]



@st.cache_data(show_spinner=False)
def full_product_catalog(
          df_skus: pd.DataFrame, 
          df_base_sku_hierarchy: pd.DataFrame, 
          df_color_pattern: pd.DataFrame, 
          df_base_sku_dimensions: pd.DataFrame, 
          df_amazon_family: pd.DataFrame
     ) -> pd.DataFrame:

     """
     Build the full product catalog by merging SKU data with hierarchy, dimensions, color patterns, and Amazon family information.

     Args:
          df_skus (pd.DataFrame): DataFrame containing SKU level information.
          df_base_sku_hierarchy (pd.DataFrame): DataFrame of base SKU hierarchies.
          df_color_pattern (pd.DataFrame): DataFrame mapping product color codes to patterns.
          df_base_sku_dimensions (pd.DataFrame): DataFrame of base SKU dimensions.
          df_amazon_family (pd.DataFrame): DataFrame mapping native families to Amazon families.

     Returns:
          pd.DataFrame: The merged DataFrame representing the full product catalog with reordered key columns.
     """

     merged_hierarchy = full_base_sku_hierarchy(df_base_sku_hierarchy, df_color_pattern)
     merged_base_sku = pd.merge(df_base_sku_dimensions, merged_hierarchy, on="base_sku", how="left")
     merged_skus = pd.merge(df_skus, merged_base_sku, on="base_sku", how="left")
     merged_amazon_family = pd.merge(merged_skus, df_amazon_family, on="native_family", how="left")

     # Reorder Columns
     reorder_cols = ['asin', 'native_family', 'amazon_family', 'sales_country_code']
     anchor_col = 'fnsku'
     reordered = reorder_after(merged_amazon_family, anchor_col, reorder_cols)

     return reordered


@st.cache_data(show_spinner=False)
def full_base_sku_hierarchy(
          base_sku_hierarchy: pd.DataFrame, 
          df_color_pattern: pd.DataFrame
     ) -> pd.DataFrame:

     """
     Merge base SKU hierarchy with color pattern data and reorder color columns.

     Args:
          base_sku_hierarchy (pd.DataFrame): DataFrame of base SKU hierarchies.
          df_color_pattern (pd.DataFrame): DataFrame mapping product color codes to color patterns.

     Returns:
          pd.DataFrame: The merged hierarchy DataFrame with color_name and color_pattern columns reordered.
     """

     # Initial Merge
     merged_hierarchy = pd.merge(base_sku_hierarchy, df_color_pattern, on='product_color_code', how='left')

     # Reorder Columns
     reorder_cols = ['color_name', 'color_pattern']
     anchor_col = 'product_color_code'
     reordered = reorder_after(merged_hierarchy, anchor_col, reorder_cols)

     return reordered


@st.cache_data(show_spinner=False)
def full_base_sku_dimensions(
          base_sku_dimensions: pd.DataFrame, 
          base_sku_hierarchy: pd.DataFrame
     ) -> pd.DataFrame:
     """
     Merge base SKU dimensions with hierarchy to include native family, and reorder accordingly.

     Args:
          base_sku_dimensions (pd.DataFrame): DataFrame of base SKU dimensions.
          base_sku_hierarchy (pd.DataFrame): DataFrame of base SKU hierarchies including native family information.

     Returns:
          pd.DataFrame: The merged dimensions DataFrame with native_family column placed after base_sku.
     """


     # Initial Merge
     base_sku_hierarchy_cols = base_sku_hierarchy[['base_sku', 'native_family']]
     merged_dimensions = pd.merge(base_sku_dimensions, base_sku_hierarchy_cols, on='base_sku', how='left')

     if 'native_family' in merged_dimensions.columns:
          cols = merged_dimensions.columns.tolist()
          cols.remove('native_family')
          base_index = cols.index('base_sku') + 1
          cols.insert(base_index, 'native_family')
          merged_dimensions = merged_dimensions[cols]
     return merged_dimensions


@st.cache_data(show_spinner=False)
def full_skus_by_amazon_family(
          df_skus: pd.DataFrame, 
          df_base_sku_hierarchy: pd.DataFrame, 
          df_amazon_family: pd.DataFrame
     ) -> pd.DataFrame:
     """
     Maps SKUs with their corresponding Amazon family by merging through base SKU hierarchy.

     Args:
          df_skus (pd.DataFrame): DataFrame containing SKU level information.
          df_base_sku_hierarchy (pd.DataFrame): DataFrame of base SKU hierarchies with asin and native_family.
          df_amazon_family (pd.DataFrame): DataFrame mapping native families to Amazon families.

     Returns:
          pd.DataFrame: DataFrame with SKU, native_family, and amazon_family mapppings.
     """

     asin_native_family = df_base_sku_hierarchy[['base_sku','asin', 'native_family']]
     merged_skus_asin = pd.merge(df_skus, asin_native_family, on='base_sku', how='left')
     merged_skus_asin_amazon_family = pd.merge(merged_skus_asin, df_amazon_family, on='native_family', how='left')

     return merged_skus_asin_amazon_family


@st.cache_data(show_spinner=False)
def full_sku_current_price_by_supplier(
          df_price_log: pd.DataFrame, 
          df_base_sku_hierarchy: pd.DataFrame, 
          color_pattern: pd.DataFrame, 
          df_price_family_by_supplier: pd.DataFrame
     ) -> pd.DataFrame:
     """
     Compute the current price of SKUs by supplier, including hierarchy, color pattern, and price family codes.

     Args:
          df_price_log (pd.DataFrame): DataFrame containing historical price log for each SKU.
          df_base_sku_hierarchy (pd.DataFrame): DataFrame of base SKU hierarchies.
          color_pattern (pd.DataFrame): DataFrame mapping product color codes to patterns.
          df_price_family_by_supplier (pd.DataFrame): DataFrame mapping SKU and supplier to price family codes.

     Returns:
          pd.DataFrame: DataFrame with the latest price information and price_family_code for each supplier and base_sku.
     """

     # Base SKU Info
     base_sku_hierarchy = full_base_sku_hierarchy(df_base_sku_hierarchy, color_pattern)
     base_sku_hierarchy = base_sku_hierarchy[['base_sku','asin', 'native_family']]

     # Price Log
     df_price_log['date'] = pd.to_datetime(df_price_log['date'])
     idx = df_price_log.groupby(['supplier', 'base_sku'])['date'].idxmax()
     current_price = df_price_log.loc[idx, ['supplier', 'base_sku', 'item_price', 'package_price', 'unit_price', 'date']].reset_index(drop=True)
     current_price['date'] = current_price['date'].dt.strftime('%Y-%m-%d')

     # Price Family by Supplier
     price_family_by_supplier = df_price_family_by_supplier[['base_sku', 'supplier','price_family_code']]

     # Merge Dataframes
     full_current_price = pd.merge(base_sku_hierarchy, current_price, on="base_sku", how="left")
     full_current_price = pd.merge(full_current_price, price_family_by_supplier, on=["base_sku", "supplier"], how="left",)

     # Reorder Columns
     reorder_cols = ['price_family_code']
     anchor_col = 'supplier'
     reordered = reorder_after(full_current_price, anchor_col, reorder_cols)

     return reordered
