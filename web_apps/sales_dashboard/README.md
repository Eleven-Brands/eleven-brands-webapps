# Sales Hourly Forecast Dashboard

This dashboard tracks sales on major event days (e.g. Prime Day) **hour by hour**, and—while an event is still in progress—**forecasts** how the rest of the day will perform based on historical hourly sales patterns.

---

## Table of Contents

1. [Overview](#overview)  
2. [Forecasting Logic](#forecasting-logic)  
   1. [1. Compute Historical Hourly Shares](#1-compute-historical-hourly-shares)  
   2. [2. Gather Today’s Actuals](#2-gather-todays-actuals)  
   3. [3. Estimate Full-Day Total](#3-estimate-full-day-total)  
   4. [4. Forecast Remaining Hours](#4-forecast-remaining-hours)  
3. [Implementation Outline](#implementation-outline)  
4. [Pseudocode Example](#pseudocode-example)  
5. [Next Steps](#next-steps)  

---

## Overview

On any given event day, we want to:
1. **Display** hourly sales that have actually occurred.  
2. While the event is still running, **forecast** the remaining hours’ sales using past-event patterns.  

To do that, we derive a “typical hourly share” from past events and then scale today’s partial-day sales up to a full‐day total.

---

## Folder Hierarchy

``` bash
sales_dashboard/
│
├── config/
│   ├── config_schema.py
│   └── event.py
│
├── pages/
│   └── 2_Amazon Family.py
│
├── shared/
│   ├── builders/
│   │   ├── all_orders.py
│   │   ├── forecasting.py
│   │   └── product_model.py
│   │
│   ├── ui/
│   │   ├── charts.py
│   │   └── sidebar.py
│   │
│   ├── bq_read.py
│   ├── data_io.py
│   └── utils.py
│
├── Home.py
└── README.md
```