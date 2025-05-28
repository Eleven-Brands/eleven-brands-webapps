"""
shared_data.py

Utilities for loading product model CSV files into Streamlit session state.

This module defines a function to load each CSV exactly once per session,
storing them under meaningful keys in `st.session_state` for downstream pages.
"""

import streamlit as st
import pandas as pd
from pathlib import Path


def get_main_path() -> Path:
    """
    Determine which MAIN_PATH exists on the user's machine.

    Checks a list of candidate directories and returns the first one that exists.

    Raises:
        FileNotFoundError: If none of the candidate paths exist.
    """
    candidate_paths = [
        Path(r'G:\Shared drives\OrganiHaus\3.1 - OH Data & Reports\product_model'),
        Path(r'G:\Drives compartilhados\OrganiHaus\3.1 - OH Data & Reports\product_model'),
    ]
    for p in candidate_paths:
        if p.exists() and p.is_dir():
            return p
    raise FileNotFoundError(
        "None of the candidate MAIN_PATH directories exist. "
        f"Tried: {', '.join(str(p) for p in candidate_paths)}"
    )


def load_csvs_once():
    """
    Load product model CSV files into Streamlit session state, once per session.

    Reads each CSV from the `MAIN_PATH` directory and assigns DataFrames to
    `st.session_state` under descriptive keys. Ensures that data loading
    occurs only once by checking and setting a `data_loaded` flag.

    Example:
        load_csvs_once()
        df_skus = st.session_state.df_skus

    Raises:
        FileNotFoundError: If any of the expected CSV files are missing.
        pandas.errors.ParserError: If CSV parsing fails for any file.
    """

    main_path = get_main_path()

    if 'data_loaded' not in st.session_state:
        st.session_state.df_amazon_family = pd.read_csv(main_path / 'td_product_model_amazon_family.csv')

        st.session_state.df_base_sku_dimensions = pd.read_csv(main_path / 'td_product_model_base_sku_dimensions.csv')
        st.session_state.df_base_sku_hierarchy = pd.read_csv(main_path / 'td_product_model_base_sku_hierarchy.csv')
        st.session_state.df_color_pattern = pd.read_csv(main_path / 'td_product_model_color_pattern.csv')

        st.session_state.df_ob_sales_marketplace = pd.read_csv(main_path / 'td_product_model_ob_amz_sales_marketplace.csv')

        st.session_state.df_price_family_by_supplier = pd.read_csv(main_path / 'td_product_model_price_family_by_supplier.csv')
        st.session_state.df_price_log = pd.read_csv(main_path / 'td_product_model_price_log.csv')

        st.session_state.df_sales_country = pd.read_csv(main_path / 'td_product_model_sales_country.csv')
        st.session_state.df_skus = pd.read_csv(main_path / 'td_product_model_skus.csv')

        st.session_state.data_loaded = True