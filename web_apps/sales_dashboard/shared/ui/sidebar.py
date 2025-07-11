"""
sidebars.py

Sidebar utilities for the Sales Dashboard Streamlit app.

This module provides the `sidebar_selector` helper to render a refresh button and Prime Day date selector
in the Streamlit sidebar, persisting the selection in session_state and returning the chosen date and event day.
"""

import streamlit as st
import datetime
from typing import Tuple

from shared.data_io import load_all_data
from shared.data_io import CSV_CONFIG


# ─── PUBLIC API ──────────────────────────────────────────────────────────────


def sidebar_selector(event_dates: dict) -> Tuple[datetime.date, int]:
    """
    Render event date selector and refresh control in the Streamlit sidebar.

    Args:
         event_dates: Mapping of label strings to datetime.date objects for available events.

    Returns:
         The selected date and the corresponding event day index (1-based).
    """

    labels = [f"{name} - {date.isoformat()}" for name, date in event_dates.items()]
    label_to_date = dict(zip(labels, event_dates.values()))

    # Initialize default selection to session state
    if "selected_date_label" not in st.session_state:
        st.session_state.selected_date_label = labels[0]

    # Style button selection for UI/UX
    st.sidebar.markdown(
        """
          <style>
          div.stButton > button[disabled] {
               background-color: #98b9d0 !important;
               color:            #4c5966 !important;    /* White text for max contrast */
               font-weight:      bold      !important;   /* Make it bolder */
               font-size:        1.1rem     !important;  /* Slightly larger */
               text-shadow:      1px 1px 2px rgba(50,50,50,0.5) !important; /* Subtle shadow */
               border-color:     #ffffff   !important;
               box-shadow:       none      !important;
               text-transform:   uppercase !important; 
          }
          </style>
          """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.button("🔄 Refresh data", on_click=_refresh_data, use_container_width=True)

        for label in labels:
            is_sel = label == st.session_state.selected_date_label
            prime_day_selection = st.button(
                label, key=label, use_container_width=True, disabled=is_sel
            )
            if prime_day_selection:
                st.session_state.selected_date_label = label
                st.rerun()

    selected_label = st.session_state.selected_date_label
    selected_date = label_to_date[selected_label]
    event_day = list(event_dates.values()).index(selected_date) + 1
    return selected_date, event_day


def sidebar_refresh() -> None:
    """
    Render refresh control in the Streamlit sidebar.

    Returns:
         The refrsh contol buttonselected date and the corresponding event day index (1-based).
    """

    with st.sidebar:
        st.button("🔄 Refresh data", on_click=_refresh_data, use_container_width=True)

    return None


def _refresh_data() -> None:
    """
    Invalidate all cached data and reset session state to force a fresh reload.

    This function does two things:
    1. Clears Streamlit's @st.cache_data cache, evicting all memoized computations
       (e.g. summaries, joins, charts, etc.).
    2. Removes every DataFrame loaded via CSV_CONFIG and the `data_loaded` sentinel
       from `st.session_state`.

    After this runs, the next Streamlit script execution will re-run your top-level
    load_all_data() calls and fetch fresh CSVs from Google Drive.
    """

    # Clear all @st.cache_data results (calculated tables, joins, charts…)
    st.cache_data.clear()

    # Pop every DataFrame and the “data_loaded” sentinel
    for key in CSV_CONFIG:
        st.session_state.pop(key, None)
    st.session_state.pop("data_loaded", None)
