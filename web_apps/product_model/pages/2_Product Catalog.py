"""
2_Product_Catalog.py

Streamlit page script for the Product Catalog interface.

This module:
- Configures the Streamlit page (title, layout)
- Handles user authentication and sidebar display
- Loads all application data
- Defines which filters (country, supplier) are disabled for each view
- Renders one tab per configured page view from the router
- Applies text and multiselect filters on SKU, native family, country, and supplier
- Displays filtered DataFrames with custom column configuration
- Provides CSV download with an option to use display name aliases
"""

import streamlit as st
from product_model.shared.shared_auth import require_login, show_user_sidebar
from product_model.shared.data_loader import load_all_data
from product_model.shared.ui_helpers import build_column_config_from_schema, combined_aliases, apply_filters
from product_model.page_config.product_catalog_router import PAGES


# ─── Initialization ────────────────────────────────────────────────────────────

st.set_page_config(page_title="Product Catalog", layout="wide")

user = require_login()
show_user_sidebar(user)

data = load_all_data()

DISABLE_CONFIG = {
     "country": {
          "Base SKU Hierarchy",
          "Base SKU Dimensions",
          "Base SKU Current Price",
     },
     "supplier": {
          "Product Catalog",
          "Base SKU Hierarchy",
          "Base SKU Dimensions",
          "SKU by Amazon Family and Country",
     },
}


# ─── Page Selector & Data Preparatio ───────────────────────────────────────────

st.title("Product Catalog")


tabs = st.tabs(list(PAGES.keys()))

for tab, (section_name, page) in zip(tabs, PAGES.items()):
     is_country_disabled = section_name in DISABLE_CONFIG["country"]
     is_supplier_disabled = section_name in DISABLE_CONFIG["supplier"]

     with tab:
          df = page.view(data)

          # ─── Filters ───────────────────────────────────────────────────────────────────
          col1, col2, col3, col4 = st.columns(4)

          with col1:
               search_base_sku = st.text_input(
                    label="Search Base SKU", 
                    placeholder='Type SKU or Base SKU...', 
                    key=f"{section_name}-search_sku"
               )

          with col2:
               native_family_list = list(data.amazon_family['native_family'].dropna().unique())
               search_native_family = st.multiselect(
                    label='Select Native Family:',
                    options=native_family_list,
                    key=f"{section_name}-search_family"
               )

          with col3:
               country_list = list(data.sales_country['sales_country_code'].dropna().unique())
               country_options = st.multiselect(
                    label="Select Country (if applicable)",
                    options=['All'] + country_list,
                    default='All',
                    placeholder='Select the country...',
                    disabled=is_country_disabled,
                    key=f"{section_name}-select_country",
               )

          with col4:
               supplier = list(data.price_family['supplier'].dropna().unique())
               supplier_options = st.multiselect(
                    label="Select Supplier (if applicable)",
                    options=['All'] + supplier,
                    default='All',
                    placeholder='Select the Supplier...',
                    disabled=is_supplier_disabled,
                    key=f"{section_name}-select_supplier",
               )


          # ─── DataFrame Display ────────────────────────────────────────────────────────
          merged_filtered = apply_filters(
               df, 
               base_sku=search_base_sku, 
               native_families=search_native_family, 
               countries=country_options, 
               suppliers=supplier_options
          )


          if merged_filtered.empty:
               st.info("No records match your filters.")
          else:
               st.dataframe(
                    merged_filtered, 
                    column_config=build_column_config_from_schema(merged_filtered, page.schema)
               )


          # ─── CSV Download ─────────────────────────────────────────────────────────────
          use_aliases = st.toggle('Use display names in CSV export', key=f"{section_name}-toggle_aliases")

          download_placeholder = st.empty()
          with st.spinner("Preparing file...", show_time=True):
               csv_data = combined_aliases(merged_filtered, page.schema) if use_aliases else merged_filtered
               csv = csv_data.to_csv(index=False).encode('utf-8')


          download_placeholder.download_button(
               label="📥 Download Table as CSV",
               data=csv,
               file_name="product_model.csv",
               mime='text/csv',
               key=f"{section_name}-download"
          )