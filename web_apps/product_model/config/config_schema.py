"""
config_schema.py

Defines the column-metadata schemas for the Streamlit Product Catalog app.

This module provides:

- `ColumnMeta` TypedDict and `Schema` alias for strong typing of column 
metadata.
- `COMMON_COLUMNS`: a shared dictionary of metadata for columns used across 
multiple tables.
- Per-table schema dictionaries that map each column name to its `type`, 
`alias`, and `help` text. 
- All schemas preserve insertion order, ensuring consistent field order in forms and tables.

Each schema can be used to:
- Configure Streamlit's `st.column_config` when displaying dataframes.
- Drive form-building or validation logic by iterating fields in the defined order.
"""

from typing import TypedDict, Dict

class ColumnMeta(TypedDict):
     type: str
     alias: str
     help: str

Schema = Dict[str, ColumnMeta]



COMMON_COLUMNS: Schema = {
     'base_sku': {
          'type': 'STRING',
          'alias': 'Base SKU',
          'help': 'Unique identifier for the product base (shared across marketplace for any given SKU).',
     },
     'product_color_code': {
          'type': 'STRING',
          'alias': 'Product Color - Code',
          'help': 'Code representing the product color. Usually, it\'s present in the SKU name.',
     },
     'native_family': {
          'type': 'STRING',
          'alias': 'Native Family',
          'help': 'TODO: fill in with team-approved description',
     },
     'supplier': {
          'type': 'STRING',
          'alias': 'Supplier',
          'help': 'The manufacturer responsible for the product production',
     },
}


TD_PRODUCT_MODEL_SKUS: Schema = {
     'base_sku': COMMON_COLUMNS['base_sku'],
     'sku': {
          'type': 'STRING',
          'alias': 'SKU',
          'help': 'Marketplace-specific SKU code.',
     },
     'fnsku': {
          'type': 'STRING',
          'alias': 'FNSKU',
          'help': 'Amazon FNSKU used in fulfillment labeling.',
     },
}


TD_PRODUCT_MODEL_BASE_SKU_DIMENSIONS: Schema = {
     'base_sku': COMMON_COLUMNS['base_sku'],
     'inner_type': {
          'type': 'STRING',
          'alias': 'Inner Type',
          'help': 'TODO: fill in with team-approved description',
     },


     # Carton Info
     'units_per_carton': {
          'type': 'INTEGER',
          'alias': 'Units/Carton',
          'help': 'Total number of units per master carton.',
     },
     'carton_weight_kg': {
          'type': 'FLOAT',
          'alias': 'Carton Weight (kg)',
          'help': 'Weight of the full carton in kilograms.',
     },
     'carton_length_cm': {
          'type': 'FLOAT',
          'alias': 'Carton Length (cm)',
          'help': 'Carton length in centimeters.',
     },
     'carton_width_cm': {
          'type': 'FLOAT',
          'alias': 'Carton Width (cm)',
          'help': 'Carton width in centimeters.',
     },
     'carton_height_cm': {
          'type': 'FLOAT',
          'alias': 'Carton Height (cm)',
          'help': 'Carton height in centimeters.',
     },
     'carton_volume_cbm': {
          'type': 'FLOAT',
          'alias': 'Carton Volume (CBM)',
          'help': 'Carton volume in cubic meters (CBM).',
     },


     # AWD Carton Info
     'awd_units_per_carton': {
          'type': 'INTEGER',
          'alias': 'AWD Units/Carton',
          'help': 'AWD-specific total number of units per master carton.',
     },
     'awd_carton_weight_kg': {
          'type': 'FLOAT',
          'alias': 'AWD Carton Weight (kg)',
          'help': 'AWD-specific weight of the full carton in kilograms.',
     },
     'awd_carton_length_cm': {
          'type': 'FLOAT',
          'alias': 'AWD Carton Length (cm)',
          'help': 'AWD-specific carton length in centimeters.',
     },
     'awd_carton_width_cm': {
          'type': 'FLOAT',
          'alias': 'AWD Carton Width (cm)',
          'help': 'AWD-specific carton width in centimeters.',
     },
     'awd_carton_height_cm': {
          'type': 'FLOAT',
          'alias': 'AWD Carton Height (cm)',
          'help': 'AWD-specific carton height in centimeters.',
     },
     'awd_carton_volume_cbm': {
          'type': 'FLOAT',
          'alias': 'AWD Carton Volume (CBM)',
          'help': 'AWD-specific carton volume in cubic meters (CBM).',
     },


     # Package Info
     'units_per_package': {
          'type': 'INTEGER',
          'alias': 'Units/Package',
          'help': 'Total number of units in a single package.',
     },
     'package_weight_kg': {
          'type': 'FLOAT',
          'alias': 'Package Weight (kg)',
          'help': 'Weight of a single package in kilograms.',
     },
     'package_length_cm': {
          'type': 'FLOAT',
          'alias': 'Package Length (cm)',
          'help': 'Package length in centimeters.',
     },
     'package_width_cm': {
          'type': 'FLOAT',
          'alias': 'Package Width (cm)',
          'help': 'Package width in centimeters.',
     },
     'package_height_cm': {
          'type': 'FLOAT',
          'alias': 'Package Height (cm)',
          'help': 'Package height in centimeters.',
     },
     'package_volume_cbm': {
          'type': 'FLOAT',
          'alias': 'Package Volume (CBM)',
          'help': 'Package volume in cubic meters (CBM).',
     },


     # Item Info
     'item_length_cm': {
          'type': 'FLOAT',
          'alias': 'Item Length (cm)',
          'help': 'Individual item length in centimeters.',
     },
     'item_width_cm': {
          'type': 'FLOAT',
          'alias': 'Item Width (cm)',
          'help': 'Individual item width in centimeters.',
     },
     'item_height_cm': {
          'type': 'FLOAT',
          'alias': 'Item Height(cm)',
          'help': 'Individual item height in centimeters.',
     },
}


TD_PRODUCT_MODEL_BASE_SKU_HIERARCHY: Schema = {
     # Product Main Info
     'base_sku': COMMON_COLUMNS['base_sku'],
     'asin': {
          'type': 'STRING',
          'alias': 'ASIN',
          'help': 'Amazon Standard Identification Number.',
     },
     'image_url': {
          'type': 'STRING',
          'alias': 'Image URL',
          'help': 'Link to the product image.',
     },
     'material': {
          'type': 'STRING',
          'alias': 'Product Material',
          'help': 'Primary material used in the product.',
     },
     'brand_code': {
          'type': 'STRING',
          'alias': 'Brand Code',
          'help': 'Two-letter code identifying the brand.',
     },
     'brand_name': {
          'type': 'STRING',
          'alias': 'Brand Name',
          'help': 'Name of the brand.',
     },

     # Product Type
     'product_main_type_code': {
          'type': 'STRING',
          'alias': 'Product Main Type - Code',
          'help': 'Code representing the main definition of the product.',
     },
     'product_main_type_name': {
          'type': 'STRING',
          'alias': 'Product Main Type - Name',
          'help': 'Descriptive name for the main product definition.',
     },
     'product_sub_type_code': {
          'type': 'STRING',
          'alias': 'Product Sub Type - Code',
          'help': 'Code for a more specific product subcategory.',
     },
     'product_sub_type_name': {
          'type': 'STRING',
          'alias': 'Product Sub Type - Name',
          'help': 'Name for the product subcategory.',
     },


     # Other Atttibutes
     'product_size_code': {
          'type': 'STRING',
          'alias': 'Product Size - Code',
          'help': 'Code indicating the product size variant.',
     },
     'product_color_code': COMMON_COLUMNS['product_color_code'],
     'product_set_quantity': {
          'type': 'INTEGER',
          'alias': 'Product Set Quantity',
          'help': 'Number of units included in a set.',
     },

     # Family Hierarchy
     'generic_family': {
          'type': 'STRING',
          'alias': 'Generic Family',
          'help': 'High-level grouping of products.',
     },
     'core_family': {
          'type': 'STRING',
          'alias': 'Core Family',
          'help': 'Core classification used for business reporting.',
     },
     'specific_family': {
          'type': 'STRING',
          'alias': 'Specific Family',
          'help': 'TODO: fill in with team-approved description',
     },
     'native_family': COMMON_COLUMNS['native_family'],
}


TD_PRODUCT_MODEL_COLOR_PATTERN: Schema = {
     'product_color_code': COMMON_COLUMNS['product_color_code'],
     'color_name': {
          'type': 'STRING',
          'alias': 'Color - Name',
          'help': 'Human-readable name of the color corresponding to the product_color_code (e.g., \'Black\', \'Sky Blue\').',
     },
     'color_pattern': {
          'type': 'STRING',
          'alias': 'Color Pattern',
          'help': 'Descriptive label for the product\'s color pattern (e.g., \'Solid\', \'Striped\', \'3-Toned\').',
     }
}


TD_PRODUCT_MODEL_AMAZON_FAMILY: Schema = {
     'native_family': COMMON_COLUMNS['native_family'],
     'sales_country_code': {
          'type': 'STRING',
          'alias': 'Sales Country - Code',
          'help': 'TODO: fill in with team-approved description',
     },
     'amazon_family': {
          'type': 'STRING',
          'alias': 'Amazon Family',
          'help': 'TODO: fill in with team-approved description',
     }
}


TD_PRODUCT_MODEL_PRICE_FAMILY_BY_SUPPLIER: Schema = {
     'supplier': COMMON_COLUMNS['supplier'],
     'base_sku': COMMON_COLUMNS['base_sku'],
     'price_family_code': {
          'type': 'STRING',
          'alias': 'Price Family - Code',
          'help': 'TODO: fill in with team-approved description',
     },
     'price_family_name': {
          'type': 'STRING',
          'alias': 'Price Family - Name',
          'help': 'TODO: fill in with team-approved description',
     }
}


TD_PRODUCT_MODEL_PRICE_LOG: Schema = {
     'date': {
          'type': 'STRING',
          'alias': 'Date',
          'help': 'TODO: fill in with team-approved description',
     },
     'supplier': COMMON_COLUMNS['supplier'],
     'base_sku': COMMON_COLUMNS['base_sku'],
     'item_price': {
          'type': 'FLOAT',
          'alias': 'Item Price',
          'help': 'TODO: fill in with team-approved description',
     },
     'package_price': {
          'type': 'FLOAT',
          'alias': 'Package Price',
          'help': 'TODO: fill in with team-approved description',
     },
     'unit_price': {
          'type': 'FLOAT',
          'alias': 'Unit Price',
          'help': 'TODO: fill in with team-approved description',
     }
}
