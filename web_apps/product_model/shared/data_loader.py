'''
data_loader.py

Utilities to load all product model data into a unified namespace.

This module wraps the call to `load_csvs_once` and assembles each
DataFrame stored in `st.session_state` into a SimpleNamespace, making
it easy to access all loaded tables via attributes.
'''

import streamlit as st
from types import SimpleNamespace
from product_model.shared.shared_data import load_csvs_once


def load_all_data() -> SimpleNamespace:
    """
    Load every product model CSV into session_state and return as attributes.

    This function ensures that the CSV files have been loaded once via
    `load_csvs_once()`, then bundles the resulting DataFrames into a
    SimpleNamespace for easy attribute-based access.

    Returns:
        SimpleNamespace: An object with the following attributes:
            - amazon_family: DataFrame of Amazon family mappings
            - base_sku_dims: DataFrame of base SKU dimensions
            - base_sku_hier: DataFrame of base SKU hierarchy
            - color_pattern: DataFrame of color pattern definitions
            - price_family: DataFrame of price family by supplier
            - price_log: DataFrame of historical price logs
            - sales_country: DataFrame of sales country codes
            - skus: DataFrame of SKUs
    """

    load_csvs_once()
    return SimpleNamespace(
        amazon_family = st.session_state.df_amazon_family,
        base_sku_dims = st.session_state.df_base_sku_dimensions,
        base_sku_hier = st.session_state.df_base_sku_hierarchy,
        color_pattern = st.session_state.df_color_pattern,
        price_family  = st.session_state.df_price_family_by_supplier,
        price_log     = st.session_state.df_price_log,
        sales_country = st.session_state.df_sales_country,
        skus          = st.session_state.df_skus,
    )