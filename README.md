# eleven-brands-webapps

Streamlit web applications for internal Eleven Brands reporting and operations. Each app lives in its own subfolder under `web_apps/`.

---

## Applications

| App | Purpose |
|-----|---------|
| [`sales_dashboard`](web_apps/sales_dashboard/README.md) | Hourly/daily sales monitoring, event-day forecasting, Amazon family view |
| [`product_model`](web_apps/product_model/) | Product catalog management — registration, updates, and validation |

---

## Running an app locally

```bash
# Sales Dashboard
streamlit run web_apps/sales_dashboard/"1_Hourly Chart.py"

# Product Model
streamlit run web_apps/product_model/Home.py
```

Each app manages its own data connections (Google Drive CSVs or Streamlit secrets). See the per-app README for configuration details.

---

## Repository Structure

```bash
eleven-brands-webapps/
└── web_apps/
    ├── sales_dashboard/          # Multi-page sales reporting app
    │   ├── 1_Hourly Chart.py     # Main entry point
    │   ├── pages/                # Additional Streamlit pages
    │   ├── config/               # Event config and column definitions
    │   ├── shared/               # Auth, data loaders, builders, UI components
    │   └── README.md             # Full app documentation
    └── product_model/            # Product catalog CRUD app
        ├── Home.py               # Main entry point
        ├── pages/                # Catalog, register, update pages
        ├── config/               # Column schema definitions
        └── shared/               # Data IO, validators, auth, UI helpers
```

---

## Getting started

Set up your local environment and GCP credentials by following [setup_local_development.md](setup_local_development.md) and [setup_gcp.md](setup_gcp.md).

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the Git workflow, code style, commit conventions, and PR process.
