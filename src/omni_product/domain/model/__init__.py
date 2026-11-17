"""Le modèle du domaine : des classes pures, sans lien avec la persistance.

Une entité porte une identité (`id` d'un type dédié).
Une valeur (Value Object) est un dataclass frozen, sans identité.
"""

from omni_product.domain.model.pricing import Amount, Discount, Price, ProductPrice, Rate
from omni_product.domain.model.procurement import (
    ProductSupply,
    RegionSupplier,
    Siren,
    SupplierByRegion,
    TvaId,
)
from omni_product.domain.model.product import (
    ImageDetail,
    ImageKey,
    NonExpiring,
    Perishable,
    Product,
    ProductId,
    ProductImage,
    ShelfLife,
    Slug,
)
from omni_product.domain.model.storage import Location, ProductStock, Quantity, Stock, Warehouse
from omni_product.domain.model.supplier import (
    ContactEmail,
    ContactPhone,
    Country,
    Region,
    Supplier,
    SupplierId,
)
from omni_product.domain.model.transport import Kilos, ProductTransport, Volume

__all__ = [
    "Amount",
    "ContactEmail",
    "ContactPhone",
    "Country",
    "Discount",
    "ImageDetail",
    "ImageKey",
    "Kilos",
    "Location",
    "NonExpiring",
    "Perishable",
    "Price",
    "Product",
    "ProductId",
    "ProductImage",
    "ProductPrice",
    "ProductStock",
    "ProductSupply",
    "ProductTransport",
    "Quantity",
    "Rate",
    "Region",
    "RegionSupplier",
    "ShelfLife",
    "Siren",
    "Slug",
    "Stock",
    "Supplier",
    "SupplierByRegion",
    "SupplierId",
    "TvaId",
    "Volume",
    "Warehouse",
]
