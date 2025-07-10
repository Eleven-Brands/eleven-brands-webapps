import streamlit as st
import pandas as pd
from pathlib import Path
import altair as alt

from shared.data_io import load_all_data
from shared.builders.all_orders import build_all_orders_full
from shared.builders.past_events_all_orders import get_last_event_all_order_analysis
from shared.auth.google_oauth import require_login, show_user_sidebar
from shared.ui.charts import event_chart
from shared.ui.metrics import compute_metrics
from shared.ui.matrices import build_st_dataframe
from shared.ui.sidebar import sidebar_refresh


from config.event import EVENT_DATES, EVENT_NAME
from config.config_schema import SALES_REGIONS



# ─── PAGE CONFIG ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="Sales Dashboard - Amazon Family", layout="wide")

user = require_login()
show_user_sidebar(user)

THIS_DIR = Path(__file__).parent
css_path = THIS_DIR.parent / "shared" / "style" / "cards.css"
st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

data = load_all_data()
event_dates = list(EVENT_DATES.values())
sidebar_refresh()

# ─── SALES REGION SELECTOR ───────────────────────────────────────────────────

sales_labels = SALES_REGIONS

if "selected_sales_region" not in st.session_state:
    st.session_state.selected_sales_region = sales_labels[0]


# create N equal columns (one for each button)
cols = st.columns(len(sales_labels)*4, gap="small")

for col, label in zip(cols, sales_labels):
    is_sel = label == st.session_state.selected_sales_region
    clicked = col.button(
        label,
        key=f"btn_{label}",
        disabled=is_sel,
        use_container_width=True
    )
    if clicked:
        st.session_state.selected_sales_region = label
        st.rerun()

selected_sales_region = st.session_state.selected_sales_region



# ─── GET DATAFRAMES ──────────────────────────────────────────────────────────

all_orders_df_analysis = build_all_orders_full()
last_event_all_orders_analysis = get_last_event_all_order_analysis(EVENT_NAME, 2024)

all_orders_df_analysis = all_orders_df_analysis[
     (all_orders_df_analysis["local_date"].isin(event_dates)) &
     (all_orders_df_analysis["sales_region"] == selected_sales_region)
]

last_event_all_orders_analysis = last_event_all_orders_analysis[
     (last_event_all_orders_analysis["sales_region"] == selected_sales_region)
]



# ─── TOP CARDS ─────────────────────────────────────────────────────────────────

# Dataframes Preparation
hourly_totals_all_orders_df_analysis = (
    all_orders_df_analysis
    .groupby(["local_date", "local_hour"], as_index=False)
    .agg(quantity=("quantity", "sum"),item_price=("item_price", "sum"))
)

last_event_hourly_totals_all_orders_df_analysis = (
    last_event_all_orders_analysis
    .groupby(["local_date", "local_hour"], as_index=False)
    .agg(quantity=("quantity", "sum"),item_price=("item_price", "sum"))
)

metrics = compute_metrics(
    all_orders_df_analysis, 
    hourly_totals_all_orders_df_analysis, 
    last_event_hourly_totals_all_orders_df_analysis
)

layout = [
    ("Total Units Sold",       "total_units_sold",     None),
    ("Total Revenue",          "total_revenue",        None),
    ("Units Sold by Hour",     "avg_units_sold",       f"{metrics['diff_units_vs_last']} vs last Prime Day"),
    ("Revenue by Hour",        "avg_revenue",          f"{metrics['diff_revenue_vs_last']} vs last Prime Day"),
]

cols = st.columns(len(layout))

for col, (label, key, delta) in zip(cols, layout):
    if delta:
        col.metric(label=label, value=metrics[key], delta=delta)
    else:
        col.metric(label=label, value=metrics[key])



# ─── CUMULATIVE SALES & TOP CATEGORIES ROW ─────────────────────────────────────

r2c1, r2c2, = st.columns(2)

r2c1.title("Top Amazon Families")

amazon_family_totals_all_orders_df_analysis = (
    all_orders_df_analysis
    .groupby(["amazon_family"], as_index=False)
    .agg(quantity=("quantity", "sum"),item_price=("item_price", "sum"))
)

chart = (
     alt.Chart(amazon_family_totals_all_orders_df_analysis)
     .mark_bar(color="#98b9d0")
     .encode(
          alt.X("quantity:Q", title="Units Sold"),
          alt.Y("amazon_family:O", sort="-x"),
     )
)
r2c1.altair_chart(chart, use_container_width=True)


r2c2.title("Daily Sales")

daily_totals_all_orders_df_analysis = (
    all_orders_df_analysis
    .groupby(["local_date"], as_index=False)
    .agg(quantity=("quantity", "sum"),item_price=("item_price", "sum"))
)

daily_totals_all_orders_df_analysis["local_date"] = pd.to_datetime(daily_totals_all_orders_df_analysis["local_date"])
daily_totals_all_orders_df_analysis["date_label"] = daily_totals_all_orders_df_analysis["local_date"].dt.strftime("%b %d")

event_chart(
    st_container=r2c2,
    all_orders_df=all_orders_df_analysis,
    date_col="local_date",
    sales_region_col="sales_region",
    selected_region=selected_sales_region,
    actual_col= "actual_quantity",
    forecast_col = "forecast_quantity",
    target_col="target_quantity"
)



# ─── ANALYSIS MATRIX ─────────────────────────────────────────────────────────

col_seg = st.columns(1)
(
    col_sku, col_family,
    col_committed_units_value, 
    col_units_operation, col_units_value, 
    col_revenue_operation, col_revenue_value
) = (
    st.columns([
        4, 4, 
        2, 
        4, 2, 
        4, 2
    ])
)



# ─── SKU SEARCH & FAMILY FILTER ──────────────────────────────────────────────

with col_seg[0]:
    group = st.segmented_control(
        label="Select Date",
        options=["Total"] + event_dates,
        selection_mode="single",
        default="Total"
    )



# ─── BUILD EVENT SALES DATAFRAME ─────────────────────────────────────────────

default_cols = ["sales_region", "amazon_family", "sku"]
group_by_cols = default_cols if group == "Total" else default_cols + ["event_date"]

event_sales = build_st_dataframe(all_orders_df_analysis, group_by_cols)
event_sales_by_amazon_family = build_st_dataframe(all_orders_df_analysis, [c for c in group_by_cols if c != "sku"])

cols = [
    "sales_region", "amazon_family", "sku", "event_date",
    "units_sold", "committed_units", "committed_diff", "progress_committed",
    "target_units", "units_diff", "progress_units_sold",
    "revenue", "target_revenue", "revenue_diff", "progress_revenue",
]
cols = [c for c in cols if c in event_sales.columns]
event_sales = event_sales[cols]
event_sales_by_amazon_family = event_sales_by_amazon_family[[c for c in cols if c != "sku"]]



# ─── FILTER BY SKU AND AMAZON FAMILY ─────────────────────────────────────────

mask = event_sales["sales_region"] == selected_sales_region
if "event_date" in event_sales.columns:
    mask &= (event_sales["event_date"] == group)

event_sales = event_sales[mask]


mask2 = event_sales_by_amazon_family["sales_region"] == selected_sales_region
if "event_date" in event_sales_by_amazon_family.columns:
    mask2 &= (event_sales_by_amazon_family["event_date"] == group)
event_sales_by_amazon_family = event_sales_by_amazon_family[mask2]



with col_sku:
    search_sku = st.text_input(
        "Search SKU",
        placeholder="Type SKU or Base SKU..."
    )

with col_family:
    search_amazon_family = st.multiselect(
        "Amazon Family",
        options=all_orders_df_analysis["amazon_family"].unique()
    )



# ─── FILTER BY UNITS SOLD PROGRESS ───────────────────────────────────────────

with col_units_operation:
    u_op = st.selectbox(
        "Units % Op.",
        ["Greater than or equal to", "Less than or equal to", "Equal to", "Between"],
        key="u_op"
    )

with col_units_value:
    u_max = float(event_sales["progress_units_sold"].max())
    if u_op == "Between":
        u_lo, u_hi = st.slider(
            "Units % Range",
            0.0, u_max, (0.0, u_max),
            step=1.0, format="%.0f"
        )
    else:
        u_val = st.number_input(
            f"Units %",
            min_value=0.0, max_value=u_max,
            value=0.0, step=1.0, format="%.0f"
        )



with col_committed_units_value:
    comm_u_max = float(event_sales["progress_units_sold"].max())
    comm_u_val = st.number_input(
        f"Min. Comm. Units",
        min_value=0.0, max_value=comm_u_max,
        value=0.0, step=1.0, format="%.0f"
    )



# ─── FILTER BY REVENUE SOLD PROGRESS ─────────────────────────────────────────

with col_revenue_operation:
    r_op = st.selectbox(
        "Revenue % Op.",
        ["Greater than or equal to", "Less than or equal to", "Equal to", "Between"],
        key="r_op"
    )

with col_revenue_value:
    r_max = float(event_sales["progress_revenue"].max())
    if r_op == "Between":
        r_lo, r_hi = st.slider(
            "Revenue % range",
            0.0, r_max, (0.0, r_max),
            step=1.0, format="%.0f"
        )
    else:
        r_val = st.number_input(
            f"Revenue %",
            min_value=0.0, max_value=r_max,
            value=0.0, step=1.0, format="%.0f"
        )



# ─── APPLY FILTER TO DATAFRAME ───────────────────────────────────────────────

df = event_sales.drop("sales_region", axis=1).copy()

if search_sku:
    df = df[df["sku"].str.contains(search_sku, case=False, na=False)]

if search_amazon_family:
    df = df[df["amazon_family"].isin(search_amazon_family)]


# Units Sold filter
if u_op == "Greater than or equal to":
    df = df[df["progress_units_sold"] >= u_val]
elif u_op == "Less than or equal to":
    df = df[df["progress_units_sold"] <= u_val]
elif u_op == "Equal to":
    df = df[df["progress_units_sold"] == u_val]
else:  # Between
    df = df[(df["progress_units_sold"] >= u_lo) &
            (df["progress_units_sold"] <= u_hi)]



# Committed Units Filter
df = df[df["committed_units"] >= comm_u_val]



# Revenue filter
if r_op == "Greater than or equal to":
    df = df[df["progress_revenue"] >= r_val]
elif r_op == "Less than or equal to":
    df = df[df["progress_revenue"] <= r_val]
elif r_op == "Equal to":
    df = df[df["progress_revenue"] == r_val]
else:  # Between
    df = df[(df["progress_revenue"] >= r_lo) &
            (df["progress_revenue"] <= r_hi)]



# ─── RENDER FILTERED TABLE ───────────────────────────────────────────────────

st.dataframe(
    df,
    hide_index=True,
    use_container_width=True,
    column_config={

        # Text Columns
        "amazon_family": st.column_config.TextColumn("Amazon Family", pinned=True),
        "sku": st.column_config.TextColumn("SKU", pinned=True),
        "event_date": st.column_config.DateColumn("Event Date", format="YYYY-MM-DD", pinned=True),

        # Units Columns
        "units_sold":          st.column_config.NumberColumn("Units Sold", format="%.0f"),

        "target_units":        st.column_config.NumberColumn("Target Units", format="%.0f"),
        "units_diff":          st.column_config.NumberColumn("Δ Units", format="%.0f"),
        "progress_units_sold": st.column_config.ProgressColumn( 
            "Units Sold / Target", format="%.0f%%",
            min_value=0.0, max_value=100
        ),

        "committed_units":        st.column_config.NumberColumn("Committed Units", format="%.0f"),
        "committed_diff":          st.column_config.NumberColumn("Δ Committed Units", format="%.0f"),
        "progress_committed": st.column_config.ProgressColumn( 
            "Units Sold / Committed Units", format="%.0f%%",
            min_value=0.0, max_value=100
        ),


        # Gross Revenue Columns
        "revenue":          st.column_config.NumberColumn("Gross Revenue", format="%.2f"),
        "target_revenue":   st.column_config.NumberColumn("Target Gross Revenue", format="%.2f"),
        "revenue_diff":     st.column_config.NumberColumn("Δ Gross Revenue", format="%.2f"),
        "progress_revenue": st.column_config.ProgressColumn(
            "Revenue / Target", format="%.0f%%",
            min_value=0.0, max_value=100
        ),
    },
)









def test():
    all_orders_df_analysis = build_all_orders_full()

    all_orders_df_analysis = all_orders_df_analysis[
     (all_orders_df_analysis["local_date"].isin(event_dates))
    ]
    event_sales = build_st_dataframe(all_orders_df_analysis, ["sales_region", "amazon_family", "sku", "event_date"])

    return event_sales.to_csv().encode("utf-8")

df_download = test()

st.download_button(
    label="Download CSV",
    data=df_download,
    file_name="data.csv",
    mime="text/csv",
    icon=":material/download:",
)



st.text("")
st.text("")
st.text("")
st.text("")
st.text("")


st.dataframe(
    event_sales_by_amazon_family,
    hide_index=True,
    use_container_width=True,
    column_config={

        # Text Columns
        "amazon_family": st.column_config.TextColumn("Amazon Family", pinned=True),
        "sku": st.column_config.TextColumn("SKU", pinned=True),
        "event_date": st.column_config.DateColumn("Event Date", format="YYYY-MM-DD", pinned=True),

        # Units Columns
        "units_sold":          st.column_config.NumberColumn("Units Sold", format="%.0f"),

        "target_units":        st.column_config.NumberColumn("Target Units", format="%.0f"),
        "units_diff":          st.column_config.NumberColumn("Δ Units", format="%.0f"),
        "progress_units_sold": st.column_config.ProgressColumn( 
            "Units Sold / Target", format="%.0f%%",
            min_value=0.0, max_value=100
        ),

        "committed_units":        st.column_config.NumberColumn("Committed Units", format="%.0f"),
        "committed_diff":          st.column_config.NumberColumn("Δ Committed Units", format="%.0f"),
        "progress_committed": st.column_config.ProgressColumn( 
            "Units Sold / Committed Units", format="%.0f%%",
            min_value=0.0, max_value=100
        ),


        # Gross Revenue Columns
        "revenue":          st.column_config.NumberColumn("Gross Revenue", format="%.2f"),
        "target_revenue":   st.column_config.NumberColumn("Target Gross Revenue", format="%.2f"),
        "revenue_diff":     st.column_config.NumberColumn("Δ Gross Revenue", format="%.2f"),
        "progress_revenue": st.column_config.ProgressColumn(
            "Revenue / Target", format="%.0f%%",
            min_value=0.0, max_value=100
        ),
    },
)
