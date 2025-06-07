"""
data_submission.py

Module responsible for processing, validating, and submitting new product data 
in a Streamlit-based Product Management application.

This module encapsulates the functionality required to:

- Prepare form submission data by cleaning, validating, and enriching it with metadata.
- Validate submitted data against existing SKUs and defined data schemas.
- Append validated data entries to persistent CSV storage.
- Manage Streamlit session state effectively, providing smooth and intuitive user interactions.

Dependencies:
- pandas
- streamlit
- uuid (for unique transaction identification)
- datetime (for timestamp metadata)
- pathlib (for file path handling)

Internal Dependencies:
- product_model.shared.data_validators (data validation and sanitation functions)
- product_model.shared.data_io (data persistence helpers and CSV path management)

This module aims for clarity, maintainability, and ease of use, both from a user 
interaction perspective and from a development and maintenance standpoint.
"""

import pandas as pd
import datetime as dt
import streamlit as st
from pathlib import Path
import uuid

# Adjust system path for project-specific imports (temporary measure, consider structured packaging)
import sys, os
sys.path.append(str(Path(os.path.abspath(__file__)).parents[2]))

from product_model.shared.data_validators import (
     _trim_trailing_empty_rows, 
     _validate_schema_datatypes, 
     validate_td_skus,
)
from product_model.shared.data_io import (
     load_all_data, 
     PATH_CSV_SKUS, 
     PATH_CSV_BASE_SKU_DIMS, 
     PATH_CSV_BASE_SKU_HIER,
)


def append_to_csv(
          df: pd.DataFrame, 
          path: Path
     ) -> None:
     """
     Append new rows from a DataFrame to an existing CSV file.

     Writes the contents of `df` to the CSV at `path` in append mode,
     omitting the header row and index. If `df` is empty, no file I/O occurs.

     Args:
          df: DataFrame containing the rows to append.
          path: Filesystem path to the target CSV file.

     Raises:
          OSError: If the file cannot be opened or written.
     """

     if not df.empty:
          try:
               df.to_csv(path, mode='a', header=False, index=False)
          except OSError as e:
               raise OSError(f"Failed to append data to {path}") from e


def reset_session_state():
     """
     Clears all keys from Streamlit's session state and immediately reruns the app.

     Use this to reset all form entries and cached data, effectively providing the user with a clean state.

     Raises:
          Streamlit rerun event to immediately restart the application script.
     """
     for key in list(st.session_state.keys()):
          del st.session_state[key]
     st.rerun()


def prepare_form_submission_df(
          key: str, 
          transaction_id: str
     ) -> pd.DataFrame:

     """
     Prepares a DataFrame from form data stored in session state for database submission.

     This function adds metadata columns (timestamps, user email, transaction ID)
     and ensures there are no trailing empty rows.

     Args:
          form_key: Key to retrieve form data from session state.
          transaction_id: Unique identifier for the current submission transaction.

     Returns:
          pd.DataFrame: Prepared DataFrame ready for submission, or empty DataFrame if no data.
     """

     df = st.session_state.form_data.get(key, pd.DataFrame()).copy()
     df = _trim_trailing_empty_rows(df)
     if df.empty:
          return df

     now = dt.datetime.now().replace(microsecond=0).isoformat()
     df['effective_start'] = now
     df['effective_end'] = dt.datetime(9999, 12, 31, 0, 0, 0).isoformat()
     df['is_current'] = True
     df['created_by'] = st.experimental_user.email
     df['created_at'] = now
     df["transaction_id"] = transaction_id

     return df


def submit_register_new_products(
          cols_skus: list, 
          cols_dims: list, 
          cols_hier: list
     ) -> None:
     """
     Handles submission for registering new products. It validates, appends new data to CSV files, and refreshes session data.

     Args:
          cols_skus (list): Columns related to SKUs for validation.
          cols_dims (list): Columns related to dimensions for validation.
          cols_hier (list): Columns related to hierarchies for validation.

     Raises:
          Streamlit error messages displayed if validation fails.
     """

     if st.button("✅ Submit All"):
          # Create Final DataFrames
          transaction_id = str(uuid.uuid4())
          new_skus   = prepare_form_submission_df(key="skus", transaction_id=transaction_id)
          new_dims   = prepare_form_submission_df(key="dims", transaction_id=transaction_id)
          new_hier   = prepare_form_submission_df(key="hier", transaction_id=transaction_id)


          # ─── Final Validation ─────────────────────────────────────────────────────────
          errors = []

          # SKUs
          existing_skus  = set(st.session_state.df_skus['sku'].dropna().astype(str).str.strip())
          existing_fnsku = set(st.session_state.df_skus['fnsku'].dropna().astype(str).str.strip())

          errs = validate_td_skus(new_skus, cols_skus, existing_skus, existing_fnsku)
          if errs:
               errors += ["— SKUs errors:"] + errs

          # Dimensions
          errs = _validate_schema_datatypes(new_dims, cols_dims)
          if errs:
               errors += ["— Dimensions errors:"] + errs

          # Hierarchy
          errs = _validate_schema_datatypes(new_hier, cols_hier, skip_required={"image_url"} )
          if errs:
               errors += ["— Hierarchy errors:"] + errs

          if errors:
               for e in errors:
                    st.error(e)
               st.error("❌ Fix the above errors before submitting.")
               st.stop()

          else:
               with st.spinner("Appending data..."):

                    if not new_skus.empty:
                         append_to_csv(new_skus, PATH_CSV_SKUS)
                    if not new_dims.empty:
                         append_to_csv(new_dims, PATH_CSV_BASE_SKU_DIMS)
                    if not new_hier.empty:
                         append_to_csv(new_hier, PATH_CSV_BASE_SKU_HIER)

                    st.session_state.pop("data_loaded", None)
                    load_all_data()

               st.success("The new products were successfully registered to the database")

               # Set session state flag to trigger reset option
               st.session_state["submitted_successfully"] = True

     if st.session_state.get("submitted_successfully", False):
          if st.button("🔄 Reset the Form"):
               reset_session_state()
               st.session_state["submitted_successfully"] = False
