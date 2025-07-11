import streamlit as st

from shared.data_io import load_all_data
from shared.builders.all_orders import build_all_orders_full
from shared.ui.sidebar import sidebar_selector
from shared.ui.charts import hourly_chart
from config.event import EVENT_DATES
from config.config_schema import SALES_REGIONS
from shared.auth.google_oauth import require_login, show_user_sidebar


# ─── INITIAL CONFIGURATION ───────────────────────────────────────────────────

st.set_page_config(page_title="Sales Dashboard - Daily Chart", layout="wide")

user = require_login()
show_user_sidebar(user)

# Load All Data
data = load_all_data()
all_orders_df = build_all_orders_full()

# Invoke sidebar selector
selected_date, event_day = sidebar_selector(EVENT_DATES)


# ─── Plot ───────────────────────────────────────────────────────────────────

row1 = st.columns(2)
row2 = st.columns(2)
columns = row1 + row2

for col, region in zip(columns, SALES_REGIONS):
    col.title(region)

    hourly_chart(
        st_container=col,
        all_orders_df=all_orders_df,
        date_col="local_date",
        sales_region_col="sales_region",
        selected_region=region,
        selected_date=selected_date,
        actual_col="cum_share_actual_quantity",
        forecast_col="cum_share_forecast_quantity",
        target_col="total_share_target_quantity",
        is_percent=True,
        has_display_labels=True,
    )
