"""Mapping impératif : relie les classes pures du domaine aux tables SQL.

Le modèle ne connaît pas ce fichier. Il est chargé à l'import du paquet `dal`, une seule fois.
"""

from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String, Table
from sqlalchemy.orm import composite

from omni_product.dal.types import vo_type
from omni_product.database import Base
from omni_product.domain.model.product import (
    NonExpiringProduct,
    PerishableProduct,
    Price,
    Product,
    ProductDiscount,
    ProductImage,
    ProductPricing,
    ProductSourcing,
    ProductStorage,
    ProductSupplierRegion,
    ProductTransport,
    RegionSupplier,
    Warehouse,
)
from omni_product.domain.model.product_values import (
    Amount,
    ContactEmail,
    ContactPhone,
    Country,
    Discount,
    DiscountId,
    ExpirationDate,
    ImageDetail,
    ImageKey,
    ImageRowId,
    Kilos,
    ProductId,
    ProductName,
    Quantity,
    Region,
    RegionRowId,
    ShelfLifeDays,
    Siren,
    Slug,
    Stock,
    SupplierId,
    SupplierName,
    TaxRate,
    TvaId,
    Volume,
    WarehouseLocation,
)
from omni_product.domain.model.supplier import Supplier

suppliers = Table(
    "suppliers",
    Base.metadata,
    Column("id", vo_type(SupplierId, String), primary_key=True),
    Column("name", vo_type(SupplierName, String)),
    Column("contact_email", vo_type(ContactEmail, String)),
    Column("contact_phone", vo_type(ContactPhone, String)),
    Column("country", vo_type(Country, String)),
    Column("region", vo_type(Region, String)),
)

# Héritage mono-table : toutes les sous-classes partagent la table `products`.
products = Table(
    "products",
    Base.metadata,
    Column("id", vo_type(ProductId, String), primary_key=True),
    Column("kind", String, nullable=False),
    Column("name", vo_type(ProductName, String), nullable=False),
    Column("slug", vo_type(Slug, String), unique=True, nullable=False),
    Column("expiration_date", vo_type(ExpirationDate, Date)),
    Column("shelf_life_days", vo_type(ShelfLifeDays, Integer)),
)

product_pricing = Table(
    "product_pricing",
    Base.metadata,
    Column("product_id", vo_type(ProductId, String), ForeignKey("products.id"), primary_key=True),
    Column("price_base", vo_type(Amount, Float)),
    Column("price_tax", vo_type(Amount, Float)),
    Column("price_tax_rate", vo_type(TaxRate, Float)),
)

product_storage = Table(
    "product_storage",
    Base.metadata,
    Column("product_id", vo_type(ProductId, String), ForeignKey("products.id"), primary_key=True),
    Column("quantity", vo_type(Quantity, Integer)),
    Column("stock", vo_type(Stock, Integer)),
    Column("warehouse_location", vo_type(WarehouseLocation, String)),
)

product_transport = Table(
    "product_transport",
    Base.metadata,
    Column("product_id", vo_type(ProductId, String), ForeignKey("products.id"), primary_key=True),
    Column("kilos", vo_type(Kilos, Float)),
    Column("volume", vo_type(Volume, String)),
)

product_sourcing = Table(
    "product_sourcing",
    Base.metadata,
    Column("product_id", vo_type(ProductId, String), ForeignKey("products.id"), primary_key=True),
    Column("supplier_id", vo_type(SupplierId, String), ForeignKey("suppliers.id")),
)

product_discounts = Table(
    "product_discounts",
    Base.metadata,
    Column("id", vo_type(DiscountId, Integer), primary_key=True, autoincrement=True),
    Column("product_id", vo_type(ProductId, String), ForeignKey("products.id"), nullable=False),
    Column("discount", vo_type(Discount, String), nullable=False),
)

product_images = Table(
    "product_images",
    Base.metadata,
    Column("id", vo_type(ImageRowId, Integer), primary_key=True, autoincrement=True),
    Column("product_id", vo_type(ProductId, String), ForeignKey("products.id"), nullable=False),
    Column("image_key", vo_type(ImageKey, String), nullable=False),
    Column("image_detail", vo_type(ImageDetail, String)),
)

product_suppliers = Table(
    "product_suppliers",
    Base.metadata,
    Column("id", vo_type(RegionRowId, Integer), primary_key=True, autoincrement=True),
    Column("product_id", vo_type(ProductId, String), ForeignKey("products.id"), nullable=False),
    Column("region", vo_type(Region, String), nullable=False),
    Column("name", vo_type(SupplierName, String)),
    Column("siren", vo_type(Siren, String)),
    Column("tva_id", vo_type(TvaId, String)),
)

_registry = Base.registry

_registry.map_imperatively(Supplier, suppliers)

_product_mapper = _registry.map_imperatively(
    Product,
    products,
    polymorphic_on=products.c.kind,
    polymorphic_identity="standard",
)
_registry.map_imperatively(
    PerishableProduct, inherits=_product_mapper, polymorphic_identity="perishable"
)
_registry.map_imperatively(
    NonExpiringProduct, inherits=_product_mapper, polymorphic_identity="non_expiring"
)

_registry.map_imperatively(
    ProductPricing,
    product_pricing,
    properties={
        "id": product_pricing.c.product_id,
        "price": composite(
            Price,
            product_pricing.c.price_base,
            product_pricing.c.price_tax,
            product_pricing.c.price_tax_rate,
        ),
    },
)
_registry.map_imperatively(ProductDiscount, product_discounts)
_registry.map_imperatively(ProductImage, product_images)
_registry.map_imperatively(
    ProductStorage,
    product_storage,
    properties={
        "id": product_storage.c.product_id,
        "warehouse": composite(Warehouse, product_storage.c.warehouse_location),
    },
)
_registry.map_imperatively(
    ProductTransport, product_transport, properties={"id": product_transport.c.product_id}
)
_registry.map_imperatively(
    ProductSourcing, product_sourcing, properties={"id": product_sourcing.c.product_id}
)
_registry.map_imperatively(
    ProductSupplierRegion,
    product_suppliers,
    properties={
        "supplier": composite(
            RegionSupplier,
            product_suppliers.c.name,
            product_suppliers.c.siren,
            product_suppliers.c.tva_id,
        )
    },
)
