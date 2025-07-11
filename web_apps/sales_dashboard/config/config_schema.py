"""
config_schema.py

This module defines core schema types and constants used across the application for
order and product modeling. It provides:

- Typed dictionaries and type aliases:
    - ColumnMeta: describes metadata for a single column (type, alias, help text).
    - Schema: mapping of column names to ColumnMeta definitions.

- Lists of supported identifiers and columns:
    - SALES_REGIONS: ISO region codes for marketplaces.
    - SYSTEM_COLS: internal system field names (audit and versioning).
    - ALL_ORDER_COLS: expected columns in raw "All Orders" tables.
    - PAST_EVENTS_COLS: expected columns in historical event orders tables.
    - SALES_CHANNEL: columns required for sales channel lookups.
    - SKU_COLS, HIERARCHY_COLS, AMAZON_FAMILY_COLS: column groups used in product
      hierarchies.
    - TARGET_COLS: expected columns for target sales by Sales Region, sku and day index
    - COMMIT_COLS: expected columns for commited units by Sales Region, sku and Date

- MARKETPLACE_TZ: mapping of country codes to language and IANA timezone strings for
  converting UTC timestamps to local timezones.

These definitions ensure consistent column naming, data validation, and timezone
handling throughout the data pipelines.
"""

from typing import TypedDict, Dict, List


class ColumnMeta(TypedDict):
    type: str
    alias: str
    help: str


Schema = Dict[str, ColumnMeta]


SALES_REGIONS: List[str] = ["US", "CA", "GB", "EU"]

MARKETPLACE_TZ = {
    # NORTH AMERICA
    "CA": {"language": "en", "to_timezone": "PST8PDT"},
    "MX": {"language": "es", "to_timezone": "America/Chihuahua"},
    "US": {"language": "en", "to_timezone": "PST8PDT"},
    # EUROPE
    "BE": {"language": "fr", "to_timezone": "Europe/Paris"},
    "DE": {"language": "de", "to_timezone": "Europe/Paris"},
    "ES": {"language": "es", "to_timezone": "Europe/Paris"},
    "FR": {"language": "fr", "to_timezone": "Europe/Paris"},
    "GB": {"language": "en", "to_timezone": "Europe/London"},
    "IE": {"language": "en", "to_timezone": "Europe/Dublin"},
    "IT": {"language": "it", "to_timezone": "Europe/Paris"},
    "NL": {"language": "nl", "to_timezone": "Europe/Paris"},
    "PL": {"language": "pl", "to_timezone": "Europe/Paris"},
    "SE": {"language": "sv", "to_timezone": "Europe/Paris"},
    "TR": {"language": "tr", "to_timezone": "Europe/Istanbul"},
}


SYSTEM_COLS = [
    "effective_start",
    "effective_end",
    "is_current",
    "created_by",
    "created_at",
    "transaction_id",
]

ALL_ORDER_COLS = [
    "amazon-order-id",
    "purchase-date",
    "order-status",
    "sales-channel",
    "sku",
    "item-status",
    "quantity",
    "currency",
    "item-price",
    "item-promotion-discount",
]

PAST_EVENTS_COLS = [
    "date_all_orders",
    "time_all_orders",
    "sales_region",
    "sales_country",
    "sku",
    "quantity",
    "item_price",
    "event_date",
    "event_name",
    "event_day",
]

SALES_CHANNEL = ["sales_channel", "sales_country_code", "sales_region"]
SKU_COLS = ["base_sku", "sku", "fnsku"]
HIERARCHY_COLS = ["base_sku", "asin", "native_family"]
AMAZON_FAMILY_COLS = ["sales_country_code", "amazon_family", "native_family"]
TARGET_COLS = ["sales_region", "sku", "day", "revenue", "units"]
COMMIT_COLS = ["sales_region", "sku", "event_date", "committed_units"]
