# eleven-brands-webapps

Streamlit web applications for internal Eleven Brands reporting and operations.

## Repository Structure

```
eleven-brands-webapps/
└── web_apps/
    ├── sales_dashboard/          # Multi-page sales monitoring and forecasting app
    │   ├── 1_Hourly Chart.py     # Main entry point (Streamlit page 1)
    │   ├── pages/                # Pages 2 (Daily Chart) and 3 (Amazon Family)
    │   ├── config/
    │   │   ├── config_schema.py  # SALES_REGIONS, MARKETPLACE_TZ, column definitions
    │   │   └── event.py          # Current event name and dates — UPDATE BEFORE EACH EVENT
    │   └── shared/
    │       ├── auth/             # Google OAuth (google_oauth.py)
    │       ├── builders/         # One builder per data domain (all_orders, forecasting, etc.)
    │       ├── ui/               # Chart, matrix, metric, and sidebar components
    │       ├── data_io.py        # CSV loaders (Google Drive file IDs via Streamlit secrets)
    │       └── utils.py          # Session state utilities
    └── product_model/            # Product catalog CRUD app
        ├── Home.py               # Main entry point
        ├── pages/                # Catalog, register, update pages
        ├── config/
        │   └── config_schema.py  # ColumnMeta TypedDict and table schemas
        └── shared/
            ├── shared_auth.py    # Auth via st.experimental_user (Streamlit native)
            ├── data_io.py        # CSV loaders (G: drive paths)
            ├── dataframe_builder.py
            ├── data_validators.py
            ├── data_submission.py
            ├── dialogs.py
            └── ui_helpers.py
```

## Key Conventions

- **Streamlit multi-page layout**: `Home.py` (or `1_*.py`) is the entry point; numbered files in `pages/` become additional pages in the sidebar.
- **Shared utilities per app**: each app has its own `shared/` folder — do not mix utilities between apps.
- **Each app is fully self-contained**: do not create cross-app imports.

## Authentication — Two Different Patterns

The two apps use different auth mechanisms — this is intentional and should not be unified without explicit instruction:

| App | Auth mechanism | File |
|-----|---------------|------|
| `sales_dashboard` | Google OAuth (custom) | `shared/auth/google_oauth.py` |
| `product_model` | `st.experimental_user` (Streamlit native) | `shared/shared_auth.py` |

## Data Sources — Hardcoded Paths

Both apps use hardcoded data source references. This is intentional:

- `sales_dashboard`: Google Drive file IDs read from Streamlit secrets (`st.secrets`) — configured in `.streamlit/secrets.toml` (gitignored).
- `product_model`: G: drive CSV paths (`G:\Shared drives\OrganiHaus\...`) — production machine maps the company Shared Drive to G:.

Do not replace these with environment variables unless explicitly asked.

## Event Configuration

`web_apps/sales_dashboard/config/event.py` defines the current sales event name and dates. **This file must be updated before each event** (Prime Day, Black Friday, etc.). It is not auto-populated.

## Claude Behavior Rules

- **Do not mix imports between apps** — each app is self-contained.
- **Do not modify auth mechanisms** without explicit instruction — the two apps intentionally use different approaches.
- **Do not commit changes** unless explicitly asked.
- When editing `event.py`, always update both `EVENT_NAME` and `EVENT_DATES` together.
