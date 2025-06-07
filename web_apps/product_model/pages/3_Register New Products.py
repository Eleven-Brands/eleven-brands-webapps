"""
3_Register New Products.py

Streamlit page for staged registration of new products into the Product Model system.

This module implements a structured, multi-step form workflow for submitting new Base SKUs, 
associated SKU identifiers, physical dimensions, and hierarchical metadata. Each section is 
validated independently and tracked through `st.session_state` to ensure data quality and user intent.

Workflow:
    Step 1 - Enter Base SKUs, SKUs, and FNSKUs
        - Validates uniqueness and required schema fields
        - Locks the section upon user confirmation

    Step 2 - Enter Base SKU Dimensions
        - Auto-populated based on validated Base SKUs
        - Schema-validated with type enforcement

    Step 3 - Enter Base SKU Hierarchy
        - Auto-populated based on validated Base SKUs
        - Optional and required fields handled accordingly

    Final Submission
        - Consolidates form data and invokes `submit_register_new_products()`
        - Data is appended to persistent storage

Features:
    - Validation dialogs to confirm irreversible actions
    - Section state tracking with session persistence
    - Form integrity enforcement and duplicate prevention
    - Expandable, dynamic sections with contextual feedback

Dependencies:
    - pandas
    - streamlit
    - product_model.shared.* modules (validation, IO, auth, UI helpers)

Usage:
    This script is part of a multi-page Streamlit app and is intended to be run as a page
    under the Streamlit multipage navigation structure (e.g., `pages/3_Register New Products.py`).
"""

import pandas as pd
import time
import streamlit as st
from typing import Sequence
from pathlib import Path

import sys, os
sys.path.append(str(Path(os.path.abspath(__file__)).parents[2]))

from product_model.shared.data_io import load_all_data
from product_model.shared.dialogs import confirm_sku_validation_dialog, confirm_reset_dialog
from product_model.shared.data_submission import submit_register_new_products
from product_model.shared.shared_auth import require_login, show_user_sidebar
from product_model.shared.ui_helpers import  build_prefilled_table, make_column_config
from product_model.shared.data_validators import _trim_trailing_empty_rows, _validate_schema_datatypes, validate_td_skus
from product_model.config.config_schema import TRACKING_CHANGE_COLUMNS, TD_PRODUCT_MODEL_SKUS, TD_PRODUCT_MODEL_BASE_SKU_DIMENSIONS, TD_PRODUCT_MODEL_BASE_SKU_HIERARCHY



# ─── Page Configuration & Definitions ────────────────────────────────────────
st.set_page_config(page_title="Register New Products", layout="wide")

cols_skus = {col: props for col, props in TD_PRODUCT_MODEL_SKUS.items() if col not in TRACKING_CHANGE_COLUMNS.keys()}
cols_dims = {col: props for col, props in TD_PRODUCT_MODEL_BASE_SKU_DIMENSIONS.items() if col not in TRACKING_CHANGE_COLUMNS.keys()}
cols_hier = {col: props for col, props in TD_PRODUCT_MODEL_BASE_SKU_HIERARCHY.items() if col not in TRACKING_CHANGE_COLUMNS.keys()}


# ─── User Authentication ─────────────────────────────────────────────────────

user = require_login()
show_user_sidebar(user)


# ─── Initial SetUp ───────────────────────────────────────────────────────────
st.title("Register New Products")
data = load_all_data()

if st.button("🔄 Clear All Inputs"):
     confirm_reset_dialog()



# ─── Section State Setup ─────────────────────────────────────────────────────
def init_section_state(
          base_skus: Sequence[str],
          state_key: str,
          schema_columns: Sequence[str],
     ) -> None:

     need_init = (
          state_key  not in st.session_state
          or set(st.session_state[state_key]["base_sku"]) != set(base_skus)
     )

     if need_init:
          if len(base_skus) > 0:
               st.session_state[state_key] = build_prefilled_table(base_skus, schema_columns)
          else:
               st.session_state[state_key] = pd.DataFrame([{col: "" for col in schema_columns}])

# General Purpose
if "form_data" not in st.session_state:
     st.session_state.form_data = {}

if "skus_df_state" not in st.session_state:
    # Start with 1000 empty rows
    st.session_state.skus_df_state = pd.DataFrame([{col: "" for col in cols_skus} for _ in range(1000)])

column_names = {
     "dims": list(cols_dims.keys()),
     "hier": list(cols_hier.keys())
}

# SKUs
skus_validated = st.session_state.get("skus_validated", False)
skus_expander_title = "✅ Step 1: Confirmed Base SKUs, SKUs and FNSKUs" if skus_validated else "Step 1: Add Base SKUs, SKUs and FNSKUs"
skus_expand_section = not skus_validated

# Dimensions
dims_is_validated = st.session_state.get("dims_is_validated", False)
dims_expander_title = "✅ Step 2: Confirmed Base SKUs Dimensions" if dims_is_validated else "Step 2: Add Base SKUs Dimensions"
dims_expand_section = not dims_is_validated

# Hierarchy
hier_is_validated = st.session_state.get("hier_is_validated", False)
hier_expander_title = "✅ Step 3: Confirmed Base SKUs Hierarchy" if hier_is_validated else "Step 3: Add Base SKUs Hierarchy"
hier_expand_section = not hier_is_validated


# ─── Step 1: SKU & FSNKU ───────────────────────────────────────────────────────

with st.expander(skus_expander_title, expanded=skus_expand_section):
     skus_df = st.data_editor(
          st.session_state.skus_df_state.copy().reset_index(drop=True).rename_axis("Row").rename(lambda x: x + 1),
          column_config=make_column_config(
               column_schema=cols_skus,
               disable_columns={"base_sku"} if skus_validated else set(),
               has_numeric_format=False,
               view_type="editor"
          ),
          hide_index=False,
          key="sku_editor_widget",
          width=700,
     )

     if st.button(label="✅ Verify SKUs", key="verify_skus"):
          existing_skus = set(data.skus['sku'].dropna().astype(str).str.strip())
          existing_fnskus = set(data.skus['fnsku'].dropna().astype(str).str.strip())
          validation_errors = validate_td_skus(skus_df, cols_skus, existing_skus, existing_fnskus)

          if validation_errors:
               for err in validation_errors:
                    st.error(err)
               st.session_state.form_data.pop("skus", None)

          else:
               st.session_state._sku_candidate_df = skus_df
               st.session_state.show_confirm_dialog = True

     if skus_validated:
             st.success("✅ SKUs section has been validated and locked.")

     if st.session_state.get("show_confirm_dialog", False):
          confirm_sku_validation_dialog()


# ─── Section State Initialization ────────────────────────────────────────────

skus_df = st.session_state.form_data.get("skus", pd.DataFrame())
base_skus = skus_df.get("base_sku", pd.Series(dtype=str)).dropna().unique()

init_section_state(base_skus, "dims_df_state", column_names["dims"])
init_section_state(base_skus, "hier_df_state", column_names["hier"])


# ─── Step 2: Base SKU Dimensions ───────────────────────────────────────────────

with st.expander(label=dims_expander_title, expanded=dims_expand_section):
     dims_df = st.data_editor(
          data=st.session_state.dims_df_state,
          column_config=make_column_config(
               column_schema=cols_dims,
               disable_columns={"base_sku"},
               has_numeric_format=False,
               view_type="editor"
          ),
          hide_index=True,
          key="dims_editor_widget",
     )

     if dims_is_validated:
          current = _trim_trailing_empty_rows(dims_df)
          snapshot = _trim_trailing_empty_rows(st.session_state.dims_df_state)
          if not current.equals(snapshot):
               st.session_state.dims_is_validated = False
               st.session_state.form_data.pop("dims", None)

     if len(base_skus) == 0:
          st.info("ℹ️ Fill and validate base SKUs to auto-fill this section with actual rows.")

     if st.button(label="✅ Verify Dimensions", key="verify_dims"):
          validation_errors = _validate_schema_datatypes(dims_df, cols_dims)

          if validation_errors:
               for err in validation_errors:
                    st.error(err)
               st.session_state.form_data.pop("dims", None)

          else:
               st.success("✅ Dimensions section has  been validated.")
               st.session_state.form_data["dims"] = dims_df
               st.session_state.dims_df_state = dims_df.copy()
               st.session_state.dims_is_validated = True
               time.sleep(1.5)
               st.rerun()


# ─── Step 3: Base SKU Hierarchy ────────────────────────────────────────────────

with st.expander(label=hier_expander_title, expanded=hier_expand_section):
     hier_df = st.data_editor(
          data=st.session_state.hier_df_state,
          column_config=make_column_config(
               column_schema=cols_hier,
               disable_columns={"base_sku"},
               has_numeric_format=False,
               view_type="editor"
          ),
          hide_index=True,
          key="hier_editor_widget",
     )

     if hier_is_validated:
          current  = _trim_trailing_empty_rows(hier_df)
          snapshot = _trim_trailing_empty_rows(st.session_state.hier_df_state)
          if not current.equals(snapshot):
               st.session_state.hier_is_validated = False
               st.session_state.form_data.pop("hier", None)

     if len(base_skus) == 0:
          st.info("ℹ️ Fill and validate base SKUs to auto-fill this section with actual rows.")

     if st.button(label="✅ Verify Hierarchy", key="verify_hier"):
          validation_errors = _validate_schema_datatypes(hier_df, cols_hier, skip_required={"image_url"})

          if validation_errors:
               for err in validation_errors:
                    st.error(err)
               st.session_state.form_data.pop("hier", None)

          else:
               st.success("✅ Hierarchy section has been validated.")
               st.session_state.form_data["hier"] = hier_df
               st.session_state.hier_df_state = hier_df.copy()
               st.session_state.hier_is_validated = True
               time.sleep(1.5)
               st.rerun()


# ─── Final Submission ──────────────────────────────────────────────────────────

st.markdown("---")

#Add Button to submit whole form
submit_register_new_products(cols_skus, cols_dims, cols_hier)