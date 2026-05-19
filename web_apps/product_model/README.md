# Product Model App

Internal Streamlit app for managing the Eleven Brands product catalog — registration, updates, and validation of product data stored in CSV files on the company Google Shared Drive.

---

## Purpose

Provides a structured UI for the data team to:
- Browse and filter the full product catalog
- Register new products with validation
- Update existing product information

---

## Folder Structure

```bash
product_model/
├── Home.py                      # Entry point — handles auth and navigation
├── pages/
│   ├── 2_Product Catalog.py     # Browse and filter the full catalog
│   ├── 3_Register New Products.py  # Form to register new SKUs
│   └── 4_Update Product Information.py  # Update fields on existing products
├── config/
│   └── config_schema.py         # ColumnMeta TypedDict, table schemas (TD_*)
├── page_config/
│   └── product_catalog_router.py  # Tab routing logic for the catalog page
└── shared/
    ├── shared_auth.py           # Auth via st.experimental_user
    ├── data_io.py               # CSV loaders — reads from G: drive paths
    ├── dataframe_builder.py     # Builds filtered DataFrames with caching
    ├── data_validators.py       # Input validation rules
    ├── data_submission.py       # Writes validated data back to CSV
    ├── dialogs.py               # Streamlit dialog components
    └── ui_helpers.py            # Reusable UI building blocks
```

---

## Running Locally

```bash
streamlit run web_apps/product_model/Home.py
```

Requires access to `G:\Shared drives\OrganiHaus\...` — the production machine maps the company Google Shared Drive to the G: drive.

---

## Authentication

Uses Streamlit's native `st.experimental_user` — no external OAuth setup required. Login is handled automatically when deployed on Streamlit Community Cloud with Google Workspace SSO configured.

---

## Data

All data is stored as CSV files on the company Google Shared Drive, accessed via G: drive paths defined in `shared/data_io.py`. Changes submitted through the app append rows or overwrite specific fields in those files.
