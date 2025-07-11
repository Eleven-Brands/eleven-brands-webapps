"""
utils.py

Utility functions for the sales dashboard Streamlit app.

This module provides helper functions for DataFrame retrieval from
Streamlit session_state and for cleaning DataFrames by removing system columns.
"""

import pandas as pd
import streamlit as st

from config.config_schema import SYSTEM_COLS


# ─── PUBLIC API ───────────────────────────────────────────────────────────────


def get_temp_df(key: str, cols: list) -> pd.DataFrame:
    """
    Load and validate the raw temp DataFrame from session state.

    Retrieves a DataFrame stored under the given session key (with system columns stripped),
    ensures it contains exactly the required columns, and returns a copy containing only
    those columns.

    Args:
         key: The session_state key where the raw temp DataFrame is stored


    Returns:
         A new DataFrame containing only the columns listed in the given list.

    Raises:
         KeyError: If any of the required columns in the give list are missing from the
         DataFrame.
    """

    df = _load_source(key)
    missing = set(cols) - set(df.columns)
    if missing:
        raise KeyError(f"Missing columns: {missing}")
    return df.loc[:, cols].copy()


# ─── READ SESSION DATAFRAMES ──────────────────────────────────────────────────


def _get_session_df(key: str) -> pd.DataFrame:
    """
    Retrieve a DataFrame stored in Streamlit's session_state by key.

    Args:
         key (str): The key in Streamlit session_state where the DataFrame data is stored.

    Returns:
         pd.DataFrame: The DataFrame corresponding to the given key.

    Raises:
         KeyError: If the specified key is not found in session_state.
    """
    try:
        data = st.session_state[key]
    except KeyError as e:
        raise KeyError(f"Session state key '{key}' not found.") from e
    return pd.DataFrame(data)


def _remove_system_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove system columns from a DataFrame.

    Filters out columns specified in SYSTEM_COLS from the DataFrame.

    Args:
         df (pd.DataFrame): The DataFrame to clean.

    Returns:
         pd.DataFrame: A new DataFrame without system columns.
    """

    return df[[col for col in df.columns if col not in SYSTEM_COLS]]


def _load_source(key: str) -> pd.DataFrame:
    """
    Load and clean a DataFrame from Streamlit's session_state by key.

    Retrieves a DataFrame stored under the given key in Streamlit's session_state,
    then removes any columns listed in SYSTEM_COLS.

    Args:
         key (str): The key in Streamlit session_state where the DataFrame data is stored.

    Returns:
         pd.DataFrame: The cleaned DataFrame without system columns.

    Raises:
         KeyError: If the specified key is not found in session_state.
    """

    return _remove_system_columns(_get_session_df(key))
