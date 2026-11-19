"""Le modèle du domaine : des entités (id typé) et des Value Objects (frozen), sans stockage."""

from omni_product.domain.model.identity import ProductId, SupplierId
from omni_product.domain.model.pricing import Amount, Price, ProductPricing, TaxRate
from omni_product.domain.model.product import (
    NonExpiring,
    Perishable,
    Product,
    ShelfLife,
    ShelfLifeDays,
    Slug,
)
from omni_product.domain.model.storage import Location, ProductStorage, Quantity, Warehouse
from omni_product.domain.model.supplier import Country, Email, Phone, Region, Supplier
from omni_product.domain.model.supply import ProductSupply, RegionSupplier, Siren, TvaId
from omni_product.domain.model.transport import (
    CarbonEmission,
    Distance,
    ProductTransport,
    TransportMode,
    Volume,
    Weight,
)

__all__ = [
    "Amount",
    "CarbonEmission",
    "Country",
    "Distance",
    "Email",
    "Location",
    "NonExpiring",
    "Perishable",
    "Phone",
    "Price",
    "Product",
    "ProductId",
    "ProductPricing",
    "ProductStorage",
    "ProductSupply",
    "ProductTransport",
    "Quantity",
    "Region",
    "RegionSupplier",
    "ShelfLife",
    "ShelfLifeDays",
    "Siren",
    "Slug",
    "Supplier",
    "SupplierId",
    "TaxRate",
    "TransportMode",
    "TvaId",
    "Volume",
    "Warehouse",
    "Weight",
]
