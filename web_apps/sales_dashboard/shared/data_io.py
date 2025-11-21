"""
data_io.py

I/O utilities for the Sales Dashboard Streamlit app, centralizing both remote
(Google Drive) and in-session data ingestion.

This module provides:
- **Google Drive integration**: Authenticates via a service account and streams
  files (including from Shared Drives) directly into memory.
- **Configurable CSV mapping**: A single `CSV_CONFIG` dict mapping logical keys
  to Drive file IDs and pandas parsing parameters.
- **Robust retry logic**: Exponential backoff and Streamlit warnings on
  transient HttpError failures.
- **Session-state caching**: Ensures each file is fetched and parsed exactly once
  per user session (`st.session_state['data_loaded']`).
- **Resource caching**: Shares one Drive client instance per session via
  `@st.cache_resource`.

Public API:
```python
load_all_data() -> FilesData
"""

import io
import time
from typing import Dict, Any
import pandas as pd
import streamlit as st
from datetime import datetime
from dataclasses import dataclass

from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload


# ─── PUBLIC API ──────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class FilesData:
    """
    Container for all DataFrames loaded by `load_all_data()`.

    Attributes:
        df_us_all_orders_temp (pd.DataFrame): US/CA/MX all-orders temp data.
        df_gb_all_orders_temp (pd.DataFrame): GB/EU all-orders temp data.
        df_sales_channel (pd.DataFrame): Sales-channel lookup data.
        df_all_orders_events (pd.DataFrame): Orders event-dates data.
        df_skus (pd.DataFrame): Product SKUs master data.
        df_base_sku_hier (pd.DataFrame): Base-SKU hierarchy data.
        df_amazon_family (pd.DataFrame): Amazon-family mapping data.
        target_primeday_2025_06 (pd.DataFrame): Target sales for Primeday Event 2025
        committed_units_2025_06 (pd.DataFrame): Committed Units for Primeday Event 2025
    """

    df_us_all_orders_temp: pd.DataFrame
    df_gb_all_orders_temp: pd.DataFrame
    df_sales_channel: pd.DataFrame
    df_all_orders_events: pd.DataFrame
    df_skus: pd.DataFrame
    df_base_sku_hier: pd.DataFrame
    df_amazon_family: pd.DataFrame
    target_primeday_2025_06: pd.DataFrame
    committed_units_2025_06: pd.DataFrame


def load_all_data() -> FilesData:
    """
    Ensure all configured CSVs are loaded into Streamlit's session_state and
    return them as a FilesData object.

    This function invokes `_load_into_session()` to read each file defined in
    `CSV_CONFIG` exactly once (guarded by an internal flag), storing the resulting
    DataFrames in `st.session_state`. It then constructs and returns a `FilesData`
    instance whose fields correspond to those session-state keys.

    Returns:
        FilesData: A frozen dataclass containing one `pd.DataFrame` for each key in
            `CSV_CONFIG`.

    Raises:
        FileNotFoundError: If any of the file paths in `CSV_CONFIG` do not exist.
        pandas.errors.ParserError: If reading any CSV fails to parse correctly.
        KeyError: If an expected key is missing from `st.session_state` after loading.
    """

    _load_into_session()
    return FilesData(**{k: st.session_state[k] for k in CSV_CONFIG})


# ─── CONFIGURATION ──────────────────────────────────────────────────────────

# Mapping of session_state keys to CSV file locations and pandas.read_csv kwargs.
CSV_CONFIG: Dict[str, Any] = {
    "df_us_all_orders_temp": {
        "file_id": "11JDuFnWReqpUmrICjjMqggYgNto4mnnq",
        "kwargs": {"sep": "\t"},
    },
    "df_gb_all_orders_temp": {
        "file_id": "11KbuTlSoGya-8JJ62srA1wKgiiZrGtt_",
        "kwargs": {"sep": "\t"},
    },
    "df_sales_channel": {"file_id": "11Mf8mVlRP-g2wjeOK0o8Hlei4Z2Kirp9", "kwargs": {}},
    "df_all_orders_events": {
        "file_id": "11laDWsPIj-UcGv6aqrjOfjv0XL7A4kJ7",
        "kwargs": {},
    },
    "df_skus": {"file_id": "1LQ5fKQw3sch6mvaPBNExtR_Yeo_cnx91", "kwargs": {}},
    "df_base_sku_hier": {"file_id": "1LNt4ozn_L9sz48cW8_6pwNpF3srVYZgH", "kwargs": {}},
    "df_amazon_family": {"file_id": "1LQAHbcOlkEbwrA-HsmZPkcHy4wyFfXYo", "kwargs": {}},

    "target_primeday_2025_06": {
        "file_id": "1dAC4rKZOh5T5TgVhUQ2WKhhFj-D_61nR",
        "kwargs": {},
    },

    "committed_units_2025_06": {
        "file_id": "1oSAUqC5OIkeK5_W0aP_sHkRw2V3Ftd6g",
        "kwargs": {},
    },
}


# ─── LOADING LOGIC ───────────────────────────────────────────────────────────


@st.cache_resource
def get_drive_service() -> Resource:
    """
    Instantiate and cache a Google Drive v3 service client using service account
    credentials.

    On first call, this function:
        1. Reads the GCP service account info from `st.secrets["gcp_service_account"]`.
        2. Creates `google.oauth2.service_account.Credentials` scoped for readonly
           Drive access.
        3. Builds and returns a `googleapiclient.discovery.Resource` for the Drive v3
           API.

    The result is cached as a resource, so subsequent calls within the same session
    reuse the same client instance rather than rebuilding it.

    Returns:
        googleapiclient.discovery.Resource: Authenticated Drive v3 service client.
    """

    creds = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/drive.readonly"],
    )
    return build("drive", "v3", credentials=creds)


def _get_drive_file_modified_time(file_id: str) -> datetime:
    drive = get_drive_service()
    metadata = (
        drive.files()
        .get(fileId=file_id, supportsAllDrives=True, fields="modifiedTime")
        .execute()
    )

    modified_dt = pd.to_datetime(metadata["modifiedTime"])

    return modified_dt.to_pydatetime()


def _load_sheet_from_drive(
    file_id: str, max_retries: int = 3, backoff_factor: float = 1.0, **read_csv_kwargs
) -> pd.DataFrame:
    """
    Download a file from Google Drive into a pandas DataFrame, retrying on failures.

    This function uses the cached Drive service client to stream the file with the
    given `file_id` into memory and parse it via `pd.read_csv`. If a `HttpError`
    occurs (e.g., transient network issues or permission errors), it will retry
    up to `max_retries` times, waiting `backoff_factor * 2**(attempt-1)` seconds
    between attempts. Each retry emits a warning in Streamlit. If all attempts
    fail, a `RuntimeError` is raised with details.

    Parameters:
        file_id: The Drive file ID to fetch.
        max_retries: Maximum download attempts before giving up. Defaults to 3.
        backoff_factor: Base seconds to wait before retrying; wait doubles
            each attempt (default: 1.0).
        **read_csv_kwargs: Additional keyword arguments passed to `pd.read_csv`
            when parsing the in-memory buffer.

    Returns:
        The DataFrame loaded from the Drive file.

    Raises:
        RuntimeError: If the file could not be fetched after `max_retries` attempts.
    """

    drive = get_drive_service()

    for attempt in range(1, max_retries + 1):
        try:

            request = drive.files().get_media(
                fileId=file_id,
                supportsAllDrives=True,
            )
            buffer = io.BytesIO()
            downloader = MediaIoBaseDownload(buffer, request)
            done = False

            while not done:
                _, done = downloader.next_chunk()

            # Parse date into dataframe
            buffer.seek(0)

            return pd.read_csv(buffer, **read_csv_kwargs)

        except HttpError as e:
            if attempt == max_retries:
                raise RuntimeError(
                    f"Could not fetch Drive file {file_id} after "
                    f"{max_retries} attempts: {e}"
                ) from e

            # Otherwise, wait then retry
            wait_seconds = backoff_factor * (2 ** (attempt - 1))
            st.warning(
                f"Attempt {attempt} for file {file_id} failed: "
                f"{e.status_code} {e.error_details}. "
                f"Retrying in {wait_seconds:.1f}s…"
            )
            time.sleep(wait_seconds)


def _load_into_session() -> None:
    """
    Load and cache all configured CSVs into Streamlit session_state exactly once.

    On the first call during a user session, this function iterates over each
    entry in CSV_CONFIG, invokes `_load_sheet_from_drive` to fetch and parse the
    file from Google Drive, and stores the resulting DataFrame in
    `st.session_state` under the corresponding key. After all files are loaded,
    it sets `st.session_state['data_loaded'] = True` so that subsequent invocations
    skip downloading and parsing entirely.

    Side Effects:
        - For each key in CSV_CONFIG, `st.session_state[key]` is populated with
          its pandas DataFrame.
        - `st.session_state['data_loaded']` is set to True.

    Raises:
        googleapiclient.errors.HttpError: If downloading any file fails (e.g.,
            due to permissions or network errors).
        pandas.errors.ParserError: If parsing a downloaded CSV into a DataFrame fails.
    """

    if not st.session_state.get("data_loaded", False):
        for key, conf in CSV_CONFIG.items():
            df = _load_sheet_from_drive(conf["file_id"], **conf["kwargs"])
            st.session_state[key] = df

            # Get Last Modified Date
            modified_dt = _get_drive_file_modified_time(conf["file_id"])
            st.session_state[f"{key}_modified_time"] = modified_dt

        st.session_state["data_loaded"] = True
