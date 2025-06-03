"""
ui_helpers.py

Utility helpers for common DataFrame UI tasks.

Exposes:
    • make_column_config            - column setup for Streamlit tables/editors
    • rename_dataframe_with_aliases - apply “alias” labels from a schema
    • filter_mask, apply_filters    - quick substring mask and multi-field filter
    • build_prefilled_table         - skeleton table for new-row entry

These functions keep view code concise by pushing repetitive logic—column
setup, alias look-ups, boolean masks, and stub-table creation—into one place.
All helpers are *pure* (they never mutate their inputs) and return new
DataFrames or dicts ready to drop into Streamlit widgets.
"""


import pandas as pd
from datetime import date
from typing import Sequence, Literal, Any
import streamlit as st


# ─── Schema Configuration ────────────────────────────────────────────────────

def make_column_config(
    *,
    column_schema: dict[str, dict],
    df_columns: Sequence[str] | None = None,
    disable_columns: set[str] = frozenset(),
    pinned_columns: set[str] | None = None,
    has_numeric_format: bool = False,
    view_type: Literal["table", "editor"] = "table"
) -> dict[str, "st.column_config.Column"]:
     """
     Build a Streamlit `column_config` mapping for either a read-only table or a data editor.

     Args:
          column_schema:  
               Mapping from column name -> metadata. Each metadata dict can contain:
               - "alias"   (str): Label shown to user  
               - "help"    (str): Tooltip/help text  
               - "type"    (str): One of "STRING", "FLOAT", or "INTEGER" (defaults to "STRING")  
          df_columns:  
               If provided, only build configs for these columns (in this exact order).  
               If None, configure all keys found in `column_schema`.
          disable_columns:  
               Columns that should be read-only (disabled) in `"editor"` mode.  
               Ignored if `view_type=="table"`.
          pinned_columns:  
               Explicit set of columns to pin at the left.  
               If None:
               - In `"table"` mode: pins "base_sku" and "sku" if they exist in df_columns.  
               - In `"editor"` mode: pins exactly those in `disable_columns`.  
          has_numeric_format:  
               If True, wrap FLOAT/INTEGER columns in a `NumberColumn(format=...)`.  
               If False, treat everything as a `TextColumn`.
          view_type:  
               - `"table"` → building a read-only table (Streamlit will never let users edit).  
               - `"editor"` → building a Streamlit data editor (some columns can be disabled, 
               others editable).

     Returns:
          dict[str, st.column_config.TextColumn | st.column_config.NumberColumn]:  
               A dict you can pass directly into `st.dataframe(..., column_config=...)`  
               or `st.data_editor(..., column_config=...)`.  
     Example:
          column_schema = {
               "sku":   {"alias": "SKU",   "help": "Stock keeping unit", "type": "STRING"},
               "price": {"alias": "Price",                   "type": "FLOAT"},
          }
          col_config = make_column_config(
               column_schema,
               df_columns=["sku","price"],
               has_numeric_format=True,
               view_type="table"
          )
          st.dataframe(df, column_config=col_config)
     """

     # Guard against incorrect view_type declaration
     if view_type not in ("table","editor"):
         raise ValueError(f"view_type must be 'table' or 'editor', got {view_type!r}")

     # Determine which columns to configure, and in what order:
     if df_columns is None:
          df_columns = list(column_schema.keys())
     else:
          df_columns = list(df_columns)

     # Handle pinned_columns logic
     if pinned_columns is None:
          if view_type == "table":
               # By default, pin "base_sku" and "sku" if they appear
               pinned_columns = {c for c in ("base_sku", "sku") if c in df_columns}
          else:
               # In editor mode, pin exactly the disabled columns
               pinned_columns = set(disable_columns) & set(df_columns)

     # Build a result dict
     config: dict[str, st.column_config.Column] = {}

     # Iterate over each column in the chosen order
     for col in df_columns:
          meta = column_schema.get(col, {})
          alias = meta.get("alias", col)
          help_text = meta.get("help", "")
          col_type = meta.get("type", "STRING").upper()

          # Set width
          if col in pinned_columns:
               width = 170
          elif col_type == "FLOAT":
               width = 150
          elif col_type == "INTEGER":
               width = 120
          elif len(alias) > 20:
               width = 200
          else:
               width = 150

          # Decide whether this column is disabled (only in editor mode)
          is_disabled = (view_type == "editor" and col in disable_columns)

          # Build common kwargs for both TextColumn and NumberColumn
          base_kwargs = {
               "label": alias, 
               "help": help_text, 
               "pinned": col in pinned_columns, 
               "width": width
          }

          if is_disabled:
               base_kwargs["disabled"] = True

          # Finally, pick which Column class to instantiate
          if col_type == "FLOAT":
               fmt = "%.2f" if has_numeric_format else None
               config[col] = st.column_config.NumberColumn(**base_kwargs, format=fmt)

          elif col_type == "INTEGER":
               fmt = "%d" if has_numeric_format else None
               config[col] = st.column_config.NumberColumn(**base_kwargs, format=fmt)

          else:
               config[col] = st.column_config.TextColumn(**base_kwargs)

     return config


def rename_dataframe_with_aliases(
          df: pd.DataFrame, 
          schema: dict[str, dict]
     ) -> pd.DataFrame:
     """
     Rename the columns of `df` according to the "alias" field in `schema`.

     Args:
          df:
               The original DataFrame whose columns you want to rename.
          schema:
               Mapping from column name -> metadata dict. If `metadata[col]["alias"]`
               exists (and is nonempty), that alias is used as the new column name;
               otherwise, the original column name is kept.

     Returns:
          A new DataFrame with the same data and index as `df`, but with columns
          renamed wherever an alias was provided in `schema`.

     Example:
          >>> df = pd.DataFrame({
          ...     "sku": ["A001", "B002"],
          ...     "price": [19.99, 25.50],
          ...     "notes": ["foo", "bar"]
          ... })
          >>> schema = {
          ...     "sku": {"alias": "SKU Code", "type": "STRING"},
          ...     "price": {"alias": "Unit Price", "type": "FLOAT"},
          ... }
          >>> renamed = rename_dataframe_with_aliases(df, schema)
          >>> renamed.columns
          Index(['SKU Code', 'Unit Price', 'notes'], dtype='object')
     """

     rename_map = {}
     for col in df.columns:
          meta = schema.get(col, {})
          alias = meta.get("alias")
          if alias:
               rename_map[col] = alias

     return df.rename(columns=rename_map)



# ─── Filters ─────────────────────────────────────────────────────────────────

def filter_mask(
          df: pd.DataFrame, 
          column: str, 
          search_str : str
     ) -> pd.Series:
     """
     Return a boolean mask indicating which rows' `column` contains `search_str` (case-insensitive).
     If `column` is missing, returns a Series of all False (same index as `df`).

     Args:
          df: 
               The DataFrame to inspect.
          column:  
               The name of the column in which to search.
          search_str:  
               The case-insensitive substring to look for.

     Returns:
          A boolean Series (same index as `df`) where True means the row's
          `column` value contains `search_str`.

     Example:
          >>> df = pd.DataFrame({
          ...     "name": ["Alice", "Bob", "Charlie"],
          ...     "city": ["Seattle", "Boston", "seattle"]
          ... })
          >>> mask = filter_mask(df, "city", "seat")
          >>> df[mask]
               name     city
          0    Alice  Seattle
          2  Charlie  seattle
     """

     if column in df.columns:
          return df[column].astype(str).str.contains(search_str, case=False, na=False)

     return pd.Series(False, index=df.index)


def apply_filters(
          df: pd.DataFrame,
          base_sku: str = None,
          native_families: list[str] = None,
          countries: list[str] = None,
          suppliers: list[str] = None
     ) -> pd.DataFrame:
     """
     Apply multiple filters to a DataFrame based on supplier, country, family, and SKU.

     Args:
          df: 
               The DataFrame to filter.
          base_sku: 
               Substring to match against 'sku' or 'base_sku' columns (case-insensitive).
               If None or empty, no base_sku filter is applied.
          native_families: 
               Filter to include only these native families; ignored if None or ['All'].
          countries: 
               Filter to include only these country codes; ignored if None or ['All'].
          suppliers: 
               Filter to include only these suppliers; ignored if None or ['All'].

     Returns:
          A filtered DataFrame containing only rows that match all specified criteria.

     Example:
          >>> df = pd.DataFrame({
          ...     "sku": ["A1", "B2", "C3"],
          ...     "base_sku": ["A", "B", "C"],
          ...     "native_family": ["F1", "F2", "F1"],
          ...     "sales_country_code": ["US", "CA", "US"],
          ...     "supplier": ["S1", "S2", "S1"]
          ... })
          >>> # Keep only rows where supplier is "S1" and country is "US"
          >>> filtered = apply_filters(df, native_families=None, countries=["US"], suppliers=["S1"], base_sku=None)
          >>> filtered
               sku base_sku native_family sales_country_code supplier
          0  A1        A            F1                  US       S1
          2  C3        C            F1                  US       S1

          >>> # Now also filter by base_sku containing "C"
          >>> filtered2 = apply_filters(df, base_sku="C", native_families=None, countries=["US"], suppliers=["S1"])
          >>> filtered2
               sku base_sku native_family sales_country_code supplier
          2  C3        C            F1                  US       S1
     """

     if "supplier" in df.columns and suppliers and suppliers != ['All']:
          df = df[df["supplier"].isin(suppliers)]

     if "sales_country_code" in df.columns and countries and countries != ['All']:
          df = df[df["sales_country_code"].isin(countries)]

     if "native_family" in df.columns and native_families and native_families != ['All']:
          df = df[df["native_family"].isin(native_families)]

     if base_sku:
          mask = (
               filter_mask(df, "sku", base_sku) |
               filter_mask(df, "base_sku", base_sku)
          )
          df = df[mask]

     return df



# ─── Aliases and Prefilling ──────────────────────────────────────────────────

def build_prefilled_table(
          base_skus: Sequence[str], 
          column_names: Sequence[str],
          fill: Any = ""
     ) -> pd.DataFrame:
     """
     Build a DataFrame with prefilled `"base_sku"` and `"date"` columns (if present).

     Each row corresponds to one element of `base_skus`.  
     If `"base_sku"` is among `column_names`, that column is set to the given value.  
     If `"date"` is among `column_names`, it's set to today's date (YYYY-MM-DD) when
     `base_sku` is nonempty; otherwise it's blank. All other columns take `fill` (or `""`
     if `fill` is None).

     Args:
          base_skus:
               A sequence of `base_sku` codes. Each element produces exactly one row's 
               `"base_sku"` value in the output DataFrame.
          column_names:
               The exact list of column names for the resulting DataFrame. The output
               will have these columns in this order.
          fill:
               The default value to use for any column *other than* `"base_sku"` and `"date"`.
               If `fill` is `None`, those cells are replaced with an empty string `""`.
               Defaults to `""`.

     Returns:
          A DataFrame with len(base_skus) rows and exactly the columns in `column_names`.  
          - If “base_sku” is present, it's filled from `base_skus`.  
          - If “date” is present, it's today's date for nonempty base_skus; else blank.  
          - All other columns take `fill` (or `""` if `fill` is None).

     Example:
          >>> base_skus = ["BASE001", "BASE002", ""]
          >>> column_names = ["base_sku", "date", "notes"]
          >>> df = build_prefilled_table(base_skus, column_names, fill="TBD")
          >>> df
               base_sku        date notes
          0  BASE001  2025-06-03   TBD
          1  BASE002  2025-06-03   TBD
          2              (blank)  (blank)
     """

     today_str = date.today().strftime('%Y-%m-%d')

     rows = []
     for base_sku in base_skus:
          row = {}
          for col in column_names:
               if col == "base_sku":
                    row[col] = base_sku
               elif col == "date":
                    row[col] = today_str if base_sku != "" else ""
               else:
                    row[col] = fill if fill is not None else ""
          rows.append(row)

     return pd.DataFrame(rows)
