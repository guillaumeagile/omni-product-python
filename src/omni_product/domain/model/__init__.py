"""Le modèle du domaine : des dataclasses qui ignorent le stockage."""

from omni_product.domain.model.pricing import Price, ProductPricing
from omni_product.domain.model.product import NonExpiringProduct, PerishableProduct, Product
from omni_product.domain.model.storage import ProductStorage, Warehouse
from omni_product.domain.model.supplier import Supplier
from omni_product.domain.model.supply import ProductSupply, RegionSupplier
from omni_product.domain.model.transport import ProductTransport

__all__ = [
    "NonExpiringProduct",
    "PerishableProduct",
    "Price",
    "Product",
    "ProductPricing",
    "ProductStorage",
    "ProductSupply",
    "ProductTransport",
    "RegionSupplier",
    "Supplier",
    "Warehouse",
]
