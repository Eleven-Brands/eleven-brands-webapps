"""
shared_io.py

Lean I/O layer for the Product-Model Streamlit app.

Exposes
- `MAIN_PATH` & `get_main_path()`   - detect the root folder on the G: drive(s).
- `PATH_CSV_*` constants            - absolute paths to each product-model CSV.
- `load_csvs_once()`                - read every CSV into `st.session_state`
                                        (df_* keys) exactly once per session.
- `load_all_data()`                 - return those DataFrames bundled in a
                                        `types.SimpleNamespace` for easy access.
"""


from pathlib import Path
from types import SimpleNamespace
import pandas as pd
import streamlit as st


# ─── CSVs Paths Constants ──────────────────────────────────────────────────────
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


MAIN_PATH = get_main_path()

PATH_CSV_AMAZON_FAMILY        = MAIN_PATH / 'td_product_model_amazon_family.csv'
PATH_CSV_BASE_SKU_DIMS        = MAIN_PATH / 'td_product_model_base_sku_dimensions.csv'
PATH_CSV_BASE_SKU_HIER        = MAIN_PATH / 'td_product_model_base_sku_hierarchy.csv'
PATH_CSV_BRANDS               = MAIN_PATH / 'td_product_model_brands.csv'
PATH_CSV_COLOR_PATTERN        = MAIN_PATH / 'td_product_model_color_pattern.csv'
PATH_CSV_OB_SALES_MARKETPLACE = MAIN_PATH / 'td_product_model_ob_amz_sales_marketplace.csv'
PATH_CSV_PRICE_FAMILY         = MAIN_PATH / 'td_product_model_price_family_by_supplier.csv'
PATH_CSV_PRICE_LOG            = MAIN_PATH / 'td_product_model_price_log.csv'
PATH_CSV_SALES_COUNTRY        = MAIN_PATH / 'td_product_model_sales_country.csv'
PATH_CSV_SKUS                 = MAIN_PATH / 'td_product_model_skus.csv'



# ─── CORE I/O FUNCTIONS ───────────────────────────────────────────────────────

def load_csvs_once() -> None:
    """
    Load product model CSV files into Streamlit session state, once per session.

    Reads from the module-level PATH_CSV_* constants and stores DataFrames
    under descriptive keys in `st.session_state`. On subsequent calls, no I/O.

    Raises:
        FileNotFoundError: If any of the expected CSV files are missing.
        pandas.errors.ParserError: If CSV parsing fails for any file.
    """

    if 'data_loaded' not in st.session_state:
        st.session_state.df_amazon_family        = pd.read_csv(PATH_CSV_AMAZON_FAMILY)
        st.session_state.df_base_sku_dims        = pd.read_csv(PATH_CSV_BASE_SKU_DIMS)
        st.session_state.df_base_sku_hier        = pd.read_csv(PATH_CSV_BASE_SKU_HIER)
        st.session_state.df_brands               = pd.read_csv(PATH_CSV_BRANDS)
        st.session_state.df_color_pattern        = pd.read_csv(PATH_CSV_COLOR_PATTERN)
        st.session_state.df_ob_sales_marketplace = pd.read_csv(PATH_CSV_OB_SALES_MARKETPLACE)
        st.session_state.df_price_family         = pd.read_csv(PATH_CSV_PRICE_FAMILY)
        st.session_state.df_price_log            = pd.read_csv(PATH_CSV_PRICE_LOG)
        st.session_state.df_sales_country        = pd.read_csv(PATH_CSV_SALES_COUNTRY)
        st.session_state.df_skus                 = pd.read_csv(PATH_CSV_SKUS)

        st.session_state.data_loaded = True


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
        base_sku_dims = st.session_state.df_base_sku_dims,
        base_sku_hier = st.session_state.df_base_sku_hier,
        color_pattern = st.session_state.df_color_pattern,
        price_family  = st.session_state.df_price_family,
        price_log     = st.session_state.df_price_log,
        sales_country = st.session_state.df_sales_country,
        skus          = st.session_state.df_skus,
    )
