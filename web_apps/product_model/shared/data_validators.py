"""
data_validators.py

Validation routines for Streamlit data-entry form.

This module provides a set of **pure** helper functions to ensure that
user-entered data conform to your application's rules before submission. 
All validators operate on **copies** of the input DataFrame and return 
a list of human-readable error messages (empty list == no errors).

Core functionality:
  - _trim_trailing_empty_rows(df)
      Remove any fully blank rows at the bottom of the sheet.
  - _validate_schema_datatypes(trimmed_df, schema, optional_fields=None)
      Enforce required-field completeness and numeric type rules
      (INTEGER, FLOAT) according to a column-metadata schema.
  - _validate_column_uniqueness(trimmed_df, column, existing, human_label)
      Generic internal + external duplicate checker for any string column.
  - validate_td_skus(df, schema, existing_skus, existing_fnskus)
      Top-level orchestration: row trimming, schema checks,
      SKU uniqueness, and FNSKU uniqueness in one call.

Dependencies:
    pandas
    typing (Set, List)

Usage example:
    errors = validate_td_skus(df, schema, existing_sku_set, existing_fnsku_set)
    if errors:
        st.error("\n".join(errors))
"""

import pandas as pd
from typing import Set, List


def _trim_trailing_empty_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Remove fully blank rows at the bottom of a DataFrame.

    A *blank* row is one in which **every** cell is an empty string after
    ``str.strip()``. The returned slice is copied, so downstream mutations
    will not affect the original ``df``.

    Args:
        df (pd.DataFrame): Frame coming from *st.data_editor*, typically
            pre-filled with real values or empty strings (no NaNs).

    Returns:
        pd.DataFrame: A new frame with trailing blank rows removed. If *df*
        contains only blank rows, an empty DataFrame (same columns/dtypes) is
        returned.
    """

    is_non_empty_row = df.apply(lambda row: row.astype(str).str.strip().ne("").any(), axis=1)
    last_valid_index = is_non_empty_row[is_non_empty_row].last_valid_index()

    if last_valid_index is None:                 # all rows blank
        return df.iloc[0:0].copy()

    return df.loc[:last_valid_index].copy()

def _validate_schema_datatypes(
        trimmed_df: pd.DataFrame, 
        schema: dict, 
        optional_fields: set = None
    ) -> list[str]:
    """
    Validate required-field completeness and numeric data types against a schema.

    For each column defined in `schema`, this function applies two rules:

    1. Required-field rule: any column **not** listed in `optional_fields` must
       have no blank cells (cells that are empty strings after `.str.strip()`).
    2. Type-specific rule: if `schema[col]["type"]` is `"INTEGER"` or `"FLOAT"`,
       values must successfully coerce via `pd.to_numeric`.  For `"INTEGER"`,
       coerced values must also have no fractional part (`value % 1 == 0`).

    Args:
        trimmed_df:
            A DataFrame whose trailing blank rows have already been removed
            Cells contain either real values or empty strings.
        schema:
            Mapping of column names to metadata dicts.  Each metadata dict
        optional_fields:
            Columns that may legally remain blank even if present in `schema`.
            Defaults to `None` (meaning all columns are required).

    Returns:
        list[str]:
            A list of human-readable error messages, one per failed validation.
            An empty list indicates that all checks passed.
    """

    optional_fields = optional_fields or set()
    errors: list[str] = []
    for col, props in schema.items():
        col_type = props.get("type")
        label = props.get("alias", col)
        series = trimmed_df[col]

        # ── Required-field rule ────────────────────────────────────────────
        if col not in optional_fields:
            if series.astype(str).str.strip().eq("").any():
                errors.append(f"❌ Column '{label}' contains empty values.")

        # ── Type-specific rules ────────────────────────────────────────────
        if col_type == "INTEGER":
            numeric = pd.to_numeric(series, errors="coerce")
            valid_mask = numeric.notna() & (numeric % 1 == 0)
            if not valid_mask.all():
                errors.append(f"❌ Column '{label}' must contain only integers.")

        elif col_type == "FLOAT":
            numeric = pd.to_numeric(series, errors="coerce")
            if not numeric.notna().all():
                errors.append(f"❌ Column '{label}' must contain valid numbers (integers or decimals).")

    return errors

def _validate_column_uniqueness(
        trimmed_df: pd.DataFrame,
        column: str,
        existing: Set[str],
        human_label: str,
    ) -> List[str]:

    """
    Check a single column for internal and external duplicates.

    This helper inspects the specified `column` in the already-trimmed DataFrame
    for two kinds of duplicate errors:

    1. **Internal duplicates**: any value that appears more than once within
       the form itself.
    2. **External duplicates**: any value that also exists in the provided
       `existing` set (e.g. values already stored in the system).

    Args:
        trimmed_df:
            A DataFrame with trailing blank rows removed, containing at least the target `column`.
        column:
            The name of the column to check for duplicates (e.g. `"sku"` or
            `"fnsku"`).
        existing:
            A set of strings representing values already recorded in the
            external system (e.g. existing SKUs/FNSKUs).
        human_label:
            A human-readable label for the values in `column`, used in error
            messages (e.g. `"SKU"` or `"FNSKU"`).

    Returns:
        List[str]:
            A list of error messages, one for internal duplicates and/or one
            for external duplicates. If no duplicates are found, the list
            will be empty.
    """

    errors: List[str] = []
    series = trimmed_df[column].dropna().astype(str).str.strip()

    # ── Internal duplicates ───────────────────────────────────────────────
    dup_mask = series.duplicated(keep=False)
    if dup_mask.any():
        msgs = [f"- {val} (row {idx})" for idx, val in series[dup_mask].items()]
        errors.append(
            f"❌ The following {human_label}s are duplicated in the form:\n"
            + "\n".join(msgs)
        )

    # ── External duplicates ───────────────────────────────────────────────
    ext_mask = series.isin(existing)
    if ext_mask.any():
        msgs = [f"- {val} (row {idx})" for idx, val in series[ext_mask].items()]
        errors.append(
            f"❌ The following {human_label}s already exist in the system:\n"
            + "\n".join(msgs)
        )

    return errors

def validate_td_skus(
        df: pd.DataFrame, 
        schema: dict, 
        existing_skus: Set[str], 
        existing_fnskus: Set[str]
    ) -> list[str]:

    """
    Run all validations for the `td_skus` data source in one call.

    This function orchestrates three checks on the provided DataFrame:

    1. **Row trimming**: Removes fully blank trailing rows.
    2. **Schema validation**: Ensures required fields are non-blank and
       numeric columns match their declared types (`INTEGER`/`FLOAT`) by
       calling `_validate_schema_datatypes`.
    3. **Uniqueness checks**: Detects internal and external duplicates in
       both the `sku` and `fnsku` columns using
       `_validate_column_uniqueness`.

    Args:
        df:
            DataFrame from `st.data_editor` containing at least the columns
            defined in `schema`, plus `sku` and `fnsku`.
        schema:
            Mapping of column names to metadata dicts for schema validation.
        existing_skus:
            Set of SKU strings already present in the system (e.g., in BigQuery).
        existing_fnskus:
            Set of FNSKU strings already present in the system.

    Returns:
        list[str]:
            A list of human-readable error messages from all validation steps.
            - If the trimmed DataFrame is empty, returns a single message
              prompting the user to add and verify rows.
            - Otherwise, returns one entry per failed rule across schema and
              uniqueness checks. An empty list indicates all validations passed.
    """

    trimmed_df = _trim_trailing_empty_rows(df)
    if trimmed_df.empty:
        return  [   f"❌ No rows to validate in this section. \n" 
                    f"Either you haven't entered any data yet, or you haven't verified "
                    f"your changes. Please add at least one row and hit “✅ Verify”."
                ]

    errors = []
    errors += _validate_schema_datatypes(trimmed_df, schema)
    errors += _validate_column_uniqueness(trimmed_df, "sku", existing_skus, "SKU")
    errors += _validate_column_uniqueness(trimmed_df, "fnsku", existing_fnskus, "FNSKU")

    return errors
