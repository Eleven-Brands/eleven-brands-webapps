"""
product_model.py

Builders for the product model.

This module provides a cached function to fetch and merge SKU, hierarchy, and
Amazon-family tables from Streamlit session_state into a single, consolidated DataFrame.
"""

import pandas as pd
import streamlit as st

from shared.utils import get_temp_df
from config.config_schema import SKU_COLS, HIERARCHY_COLS, AMAZON_FAMILY_COLS

# ─── PUBLIC API ───────────────────────────────────────────────────────────────


@st.cache_data
def get_product_model() -> pd.DataFrame:
    """
    Fetch and merge SKU, hierarchy, and Amazon-family tables from session_state.

    This function reads three DataFrames stored under the keys
    'df_skus', 'df_base_sku_hier', and 'df_amazon_family' in Streamlit's session_state.
    It performs left joins on 'base_sku' and 'native_family' to combine these tables.

    Returns:
         A consolidated DataFrame with the following columns:
              - base_sku
              - sku
              - fnsku
              - asin
              - native_family
              - sales_country_code
              - amazon_family

    Raises:
         KeyError: If any required session_state key is missing or if expected columns
                   are not present in the loaded DataFrames.
    """

    skus = get_temp_df("df_skus", SKU_COLS)
    base_sku_hier = get_temp_df("df_base_sku_hier", HIERARCHY_COLS)
    amazon_family = get_temp_df("df_amazon_family", AMAZON_FAMILY_COLS)

    merged = skus.merge(base_sku_hier, on="base_sku", how="left")
    merged = merged.merge(amazon_family, on="native_family", how="left")

    return merged[
        [
            "base_sku",
            "sku",
            "fnsku",
            "asin",
            "native_family",
            "sales_country_code",
            "amazon_family",
        ]
    ]
