# Sales Dashboard

Streamlit dashboard for tracking sales on major event days (e.g. Prime Day) with hourly actuals and an in-progress day forecast based on historical patterns.

---

## Table of Contents

1. [Overview](#overview)
2. [Forecasting Logic](#forecasting-logic)
   1. [1. Compute Historical Hourly Shares](#1-compute-historical-hourly-shares)
   2. [2. Gather Today's Actuals](#2-gather-todays-actuals)
   3. [3. Estimate Full-Day Total](#3-estimate-full-day-total)
   4. [4. Forecast Remaining Hours](#4-forecast-remaining-hours)
3. [Folder Hierarchy](#folder-hierarchy)
4. [Setup & Running](#setup--running)

---

## Overview

On any given event day, we want to:
1. **Display** hourly sales that have actually occurred.
2. While the event is still running, **forecast** the remaining hours' sales using past-event patterns.

To do that, we derive a "typical hourly share" from past events and then scale today's partial-day sales up to a full-day total.

---

## Forecasting Logic

### 1. Compute Historical Hourly Shares

For each past event, compute the fraction of total daily sales that occurred in each hour:

```
share_h = sales_h / total_daily_sales   (for each hour h in each past event)
```

Average these shares across all past events to get a stable baseline:

```
avg_share_h = mean(share_h)   across past events
```

### 2. Gather Today's Actuals

Collect the real hourly sales figures reported so far for the current event day, up to the most recently completed hour.

### 3. Estimate Full-Day Total

Use the actuals to back-calculate an implied full-day total:

```
implied_total = sum(actual_h) / sum(avg_share_h for completed hours)
```

### 4. Forecast Remaining Hours

Apply the historical share to the implied total for each remaining hour:

```
forecast_h = implied_total * avg_share_h   (for each not-yet-completed hour h)
```

---

## Folder Hierarchy

```bash
sales_dashboard/
│
├── 1_Hourly Chart.py        # Main Streamlit app — home page (hourly view)
│
├── pages/
│   ├── 2_Daily Chart.py     # Daily aggregated sales chart
│   └── 3_Amazon Family.py   # Amazon product family view
│
├── config/
│   ├── config_schema.py     # Configuration schema definitions
│   └── event.py             # Event definitions and date configuration
│
├── shared/
│   ├── auth/
│   │   └── google_oauth.py  # Google OAuth authentication
│   ├── builders/
│   │   ├── all_orders.py
│   │   ├── committed_units.py
│   │   ├── consolidation.py
│   │   ├── forecasting.py
│   │   ├── past_events_all_orders.py
│   │   ├── product_model.py
│   │   └── target_sales.py
│   ├── style/
│   │   └── cards.css        # Card component styles
│   ├── ui/
│   │   ├── charts.py
│   │   ├── matrices.py
│   │   ├── metrics.py
│   │   └── sidebar.py
│   ├── data_io.py           # BigQuery data loading
│   └── utils.py
│
└── README.md
```

---

## Setup & Running

### 1. Set up your environment

Follow [setup_local_development.md](../../setup_local_development.md) for the full local setup guide.

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Authenticate with GCP

Follow [setup_gcp.md](../../setup_gcp.md) to install the Google Cloud SDK and authenticate.

```bash
gcloud auth application-default login
```

### 3. Run the dashboard

From within the `sales_dashboard/` directory:

```bash
streamlit run "1_Hourly Chart.py"
```
