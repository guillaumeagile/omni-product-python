"""Le modèle du domaine : des classes pures, sans lien avec la persistance.

Une entité porte une identité (`id` d'un type dédié).
Une valeur (Value Object) est un dataclass frozen, sans identité.
"""

from omni_product.domain.model.pricing import (
    Amount,
    Discount,
    Price,
    PrixAvecTaxe,
    PrixHorsTaxe,
    ProductPrice,
    Rate,
    prix_of,
)
from omni_product.domain.model.procurement import (
    IdentifiantLegal,
    ProductSupply,
    RegionSupplier,
    Siren,
    SupplierByRegion,
    TvaId,
    region_supplier_of,
)
from omni_product.domain.model.product import (
    ImageDetail,
    ImageKey,
    NonExpiring,
    ParDateEtDuree,
    ParDateLimite,
    ParDureeDeConservation,
    Perishable,
    Product,
    ProductId,
    ProductImage,
    ShelfLife,
    ShelfLifeDays,
    Slug,
    date_limite,
    perissable_of,
)
from omni_product.domain.model.storage import Location, ProductStock, Quantity, Stock, Warehouse
from omni_product.domain.model.supplier import Region, Supplier, SupplierId
from omni_product.domain.model.transport import (
    Charge,
    Kilos,
    ProductTransport,
    Volume,
    charge_of,
)

__all__ = [
    "Amount",
    "Charge",
    "Discount",
    "IdentifiantLegal",
    "ImageDetail",
    "ImageKey",
    "Kilos",
    "Location",
    "NonExpiring",
    "ParDateEtDuree",
    "ParDateLimite",
    "ParDureeDeConservation",
    "Perishable",
    "Price",
    "PrixAvecTaxe",
    "PrixHorsTaxe",
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
    "ShelfLifeDays",
    "Siren",
    "Slug",
    "Stock",
    "Supplier",
    "SupplierByRegion",
    "SupplierId",
    "TvaId",
    "Volume",
    "Warehouse",
    "charge_of",
    "date_limite",
    "perissable_of",
    "prix_of",
    "region_supplier_of",
]
