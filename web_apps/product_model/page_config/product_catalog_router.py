"""
product_catalog_router.py

This module defines the available product catalog pages for the Streamlit app by
mapping view functions to their required data sources and schema metadata.
"""

from dataclasses import dataclass
from typing import Callable, List, Dict, Any
import pandas as pd

from product_model.shared.dataframe_builder import (
    full_product_catalog,
    full_base_sku_hierarchy,
    full_base_sku_dimensions,
    full_skus_by_amazon_family,
    full_sku_current_price_by_supplier,
)
from product_model.config.config_schema import (
    TD_PRODUCT_MODEL_SKUS,
    TD_PRODUCT_MODEL_BASE_SKU_HIERARCHY,
    TD_PRODUCT_MODEL_BASE_SKU_DIMENSIONS,
    TD_PRODUCT_MODEL_COLOR_PATTERN,
    TD_PRODUCT_MODEL_AMAZON_FAMILY,
    TD_PRODUCT_MODEL_PRICE_LOG,
    TD_PRODUCT_MODEL_PRICE_FAMILY_BY_SUPPLIER,
)

@dataclass
class Page:
    """
    Represents a catalog page configuration.

    Attributes:
        func (Callable[..., pd.DataFrame]): Function that produces the page DataFrame.
        args (List[str]): Names of attributes on the data object to pass as inputs.
        schema (Dict[str, dict]): Schema metadata for configuring column displays.
    """

    func: Callable[..., pd.DataFrame]
    args: List[str]             # names of attributes on your `data` object
    schema: Dict[str, dict]

    def view(self, data: Any) -> pd.DataFrame:
        """
        Execute the view function using attributes from the data object.

        Args:
            data (Any): An object whose attributes correspond to the 'args' list,
                each providing a DataFrame input to the view function.

        Returns:
            pd.DataFrame: The DataFrame returned by the view function.

        Raises:
            AttributeError: If any expected attribute is missing on the data object.
        """

        # Validate that all required attributes exist on data
        missing = [attr for attr in self.args if not hasattr(data, attr)]
        if missing:
            page_name = getattr(self.func, "__name__", "<unknown>")
            missing_attrs = ", ".join(missing)
            raise AttributeError(
                f"Page '{page_name}' expected data attribute(s) [{missing_attrs}] not found on the data object."
            )

        # Gather inputs and call the view function
        inputs = [getattr(data, attr) for attr in self.args]
        return self.func(*inputs)


PAGES: dict[str, Page] = {
    "Product Catalog": Page(
        func=full_product_catalog,
        args=["skus", "base_sku_hier", "color_pattern", "base_sku_dims", "amazon_family"],
        schema={
            **TD_PRODUCT_MODEL_SKUS,
            **TD_PRODUCT_MODEL_BASE_SKU_HIERARCHY,
            **TD_PRODUCT_MODEL_BASE_SKU_DIMENSIONS,
            **TD_PRODUCT_MODEL_COLOR_PATTERN,
            **TD_PRODUCT_MODEL_AMAZON_FAMILY,
        },
    ),
    "Base SKU Hierarchy": Page(
        func=full_base_sku_hierarchy,
        args=["base_sku_hier", "color_pattern"],
        schema=TD_PRODUCT_MODEL_BASE_SKU_HIERARCHY,
    ),
    "Base SKU Dimensions": Page(
        func=full_base_sku_dimensions,
        args=["base_sku_dims", "base_sku_hier"],
        schema={**TD_PRODUCT_MODEL_BASE_SKU_DIMENSIONS, **TD_PRODUCT_MODEL_AMAZON_FAMILY},
    ),
    "Base SKU Current Price": Page(
        func=full_sku_current_price_by_supplier,
        args=["price_log", "base_sku_hier", "color_pattern", "price_family"],
        schema={
            **TD_PRODUCT_MODEL_PRICE_LOG,
            **TD_PRODUCT_MODEL_BASE_SKU_HIERARCHY,
            **TD_PRODUCT_MODEL_COLOR_PATTERN,
            **TD_PRODUCT_MODEL_PRICE_FAMILY_BY_SUPPLIER,
        },
    ),
    "SKU by Amazon Family and Country": Page(
        func=full_skus_by_amazon_family,
        args=["skus", "base_sku_hier", "amazon_family"],
        schema={**TD_PRODUCT_MODEL_SKUS, **TD_PRODUCT_MODEL_BASE_SKU_HIERARCHY, **TD_PRODUCT_MODEL_AMAZON_FAMILY},
    ),
}


