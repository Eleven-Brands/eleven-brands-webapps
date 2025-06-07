"""
Streamlit confirmation dialogs for critical user actions.

This module defines reusable dialog components for the Product Model app using 
Streamlit's `@st.dialog` decorator. These dialogs are used to confirm irreversible 
actions such as locking Base SKUs or resetting the entire form, helping users 
make intentional decisions and minimizing data loss.

Functions:
    confirm_sku_validation_dialog():
        Displays a confirmation dialog to lock Base SKUs and finalize SKU input.

    confirm_reset_dialog():
        Displays a confirmation dialog to reset all session inputs and restart the form.

Usage:
    These functions are typically triggered by boolean flags in `st.session_state` 
    (e.g., `show_confirm_dialog`) and are rendered as modal dialogs. Upon user 
    confirmation, session state is updated accordingly and the app is re-run.

Dependencies:
    - streamlit
    - time
    - product_model.shared.data_submission.reset_session_state

Assumptions:
    The calling context is responsible for ensuring that the following session state 
    keys are initialized before invoking the dialogs:
        - st.session_state._sku_candidate_df
        - st.session_state.form_data
"""

import time
import streamlit as st
from product_model.shared.data_submission import reset_session_state


@st.dialog("⚠️ Confirm Base SKUs Lock")
def confirm_sku_validation_dialog():
    """
    Display a confirmation dialog to lock Base SKUs, making them non-editable.

    This action updates session state variables to finalize SKUs and 
    prevent further modifications.

    Session State Updates:
        - skus_validated: Marks SKUs as validated (bool).
        - skus_df_state: Stores validated SKUs DataFrame.
        - form_data["skus"]: Updates form data with candidate SKUs.

    User Interaction:
        - On cancel: Closes dialog without changes.
        - On confirm: Locks SKUs, displays success message, updates session state, and reruns app.
    """

    st.write("Are you sure you want to proceed? You won't be able to edit Base SKUs afterward.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("❌ Cancel"):
            st.session_state.show_confirm_dialog = False
            st.rerun()

    with col2:
        if st.button("✅ Yes, Lock SKUs"):
            st.success("✅ SKUs data validated and locked.")
            st.session_state.form_data["skus"] = st.session_state._sku_candidate_df
            st.session_state.skus_df_state = st.session_state._sku_candidate_df.copy()
            st.session_state.skus_validated = True
            st.session_state.show_confirm_dialog = False
            time.sleep(1.5)
            st.rerun()


@st.dialog("⚠️ Confirm Reset", width="large")
def confirm_reset_dialog():
    """
    Display a confirmation dialog to reset all inputs and restart the data-entry process.

    User Interaction:
        - On cancel: Closes dialog, retains all current inputs.
        - On confirm: Clears session state, displays a success message, pauses briefly, 
                      resets the state, and reruns app, resulting in all input data being lost.
    """

    confirm_text = "Are you sure you want to reset and start over? This will erase all inputs."
    cancel_label = "❌ No, I want to keep editing!"
    yes_label = "✅ Yes, Reset Now!"

    st.write(confirm_text)

    col1, col2 = st.columns(2)
    with col1:
        st.write("")
        if st.button(cancel_label):
            st.rerun()

    with col2:
        st.write("")
        if st.button(yes_label):
            st.success("✅ Erasing Data")
            time.sleep(1.5)
            reset_session_state()
            st.rerun()
