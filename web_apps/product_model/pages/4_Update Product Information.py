import pandas as pd
import time
import streamlit as st
from pathlib import Path

import sys, os
sys.path.append(str(Path(os.path.abspath(__file__)).parents[2]))


from product_model.shared.shared_auth import require_login, show_user_sidebar
from product_model.shared.data_io import load_all_data
from product_model.shared.ui_helpers import make_column_config
from product_model.config.config_schema import (
    TRACKING_CHANGE_COLUMNS,
    TD_PRODUCT_MODEL_BASE_SKU_DIMENSIONS,
    TD_PRODUCT_MODEL_SKUS,
    TD_PRODUCT_MODEL_BASE_SKU_HIERARCHY,
)

# ─── Page Configuration & Definitions ────────────────────────────────────────
st.set_page_config(page_title="Update Product Information", layout="wide")




# ─── User Authentication ─────────────────────────────────────────────────────

user = require_login()
show_user_sidebar(user)

TABLE_GROUPS = {
    "Product Info": ["td_product_model_base_sku_dimensions", "td_product_model_base_sku_hierarchy", "td_product_model_skus", "td_product_model_amazon_family"],
    "Supplier Info": ["td_product_model_price_log", "td_product_model_price_family_by_supplier"],
    "Commercial Settings": ["td_product_model_brands", "td_product_model_sales_country", "td_product_model_color_pattern", "td_product_model_ob_amz_sales_marketplace"],
}

TABLE_LABELS = {
    "td_product_model_base_sku_dimensions": "Base SKU Dimensions",
    "td_product_model_base_sku_hierarchy": "Base SKU Hierarchy",
    "td_product_model_skus": "SKUs",
    "td_product_model_amazon_family": "Amazon Family",
    "td_product_model_price_log": "Price Log",
    "td_product_model_price_family_by_supplier": "Price by Supplier",
    "td_product_model_brands": "Brands",
    "td_product_model_sales_country": "Sales Country",
    "td_product_model_color_pattern": "Color Pattern",
    "td_product_model_ob_amz_sales_marketplace": "Amazon Marketplaces",
}

























# Layout: sidebar (1 column), main area (3 columns width)
nav_col, content_col = st.columns([1, 5], gap="large")

# ───────────── Custom "Sidebar" Navigation ─────────────



with nav_col:
     st.markdown(
          """
          <style>
               div.stButton > button[disabled] {
                    background-color: #0066cc !important;
                    color: #ffffff !important;
                    border-color: #ffffff !important;
                    box-shadow: none !important;
               }
          </style>
          """,
          unsafe_allow_html=True,
     )

     st.markdown("### Update Information")

     # callback to set the selection
     def _select(table_id):
          st.session_state.selected_table = table_id

     for group_title, table_ids in TABLE_GROUPS.items():
          st.markdown(f"#### {group_title}")
          for table_id in table_ids:
               label = TABLE_LABELS[table_id]
               is_selected = st.session_state.get("selected_table") == table_id

               st.button(
                    label,
                    key=f"nav_{table_id}",
                    use_container_width=True,
                    disabled=is_selected,
                    on_click=_select,
                    args=(table_id,),
               )
          st.markdown("---")












with content_col:
    if "selected_table" not in st.session_state:
        st.info("⬅️ Select a table to start editing.")
    else:
        table_id = st.session_state.selected_table
        st.subheader(f"Editing: {TABLE_LABELS.get(table_id, table_id)}")

        # --- Base SKU Dimensions editor ---
        if table_id == TD_PRODUCT_MODEL_BASE_SKU_DIMENSIONS:
            data = load_all_data()
            df_orig = data.base_sku_dims.copy()
            schema = TD_PRODUCT_MODEL_BASE_SKU_DIMENSIONS
            col_config = make_column_config(df_orig, schema)
            edited_df = st.data_editor(
                df_orig,
                column_config=col_config,
                hide_index=True,
                use_container_width=True,
            )

            if st.button("Save changes"):
                diff = df_orig.ne(edited_df)
                changed = diff.any(axis=1)
                if not changed.any():
                    st.info("No changes detected.")
                else:
                    now = pd.Timestamp.now()
                    rows = []
                    for idx in df_orig.index[changed]:
                        old = df_orig.loc[idx]
                        new = edited_df.loc[idx]
                        for col in diff.columns[diff.loc[idx]]:
                            if col in TRACKING_CHANGE_COLUMNS:
                                continue
                            rows.append({
                                "table_name": TD_PRODUCT_MODEL_BASE_SKU_DIMENSIONS,
                                "primary_key": old.get("base_sku"),
                                "column_name": col,
                                "old_value": old[col],
                                "new_value": new[col],
                                "changed_by": user.get("email"),
                                "changed_at": now,
                            })
                    changes_df = pd.DataFrame(rows)
                    # TODO: persist `changes_df` to your change log
                    st.success(f"{len(rows)} change(s) prepared for persistence.")

        # --- Other tables placeholder ---
        else:
            st.info(f"Editor for `{TABLE_LABELS.get(table_id, table_id)}` coming soon.")



