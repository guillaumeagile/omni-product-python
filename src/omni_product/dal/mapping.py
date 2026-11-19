"""Le branchement du modèle sur la base : tables et mapping impératif SQLAlchemy.

Le modèle (`domain/model/`) ne connaît pas SQLAlchemy. Ce module décrit les tables et y
branche les dataclasses du domaine de l'extérieur, une seule fois, à l'import.
"""

from dataclasses import asdict
from typing import Any, override

from sqlalchemy import (
    JSON,
    Column,
    Date,
    Dialect,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    TypeDecorator,
)
from sqlalchemy.orm import composite, registry

from omni_product.domain.model import (
    NonExpiringProduct,
    PerishableProduct,
    Price,
    Product,
    ProductPricing,
    ProductStorage,
    ProductSupply,
    ProductTransport,
    RegionSupplier,
    Supplier,
    Warehouse,
)


class _RegionSuppliers(TypeDecorator[dict[str, RegionSupplier]]):
    """Les fournisseurs par région, rangés en JSON : `{région: {name, siren, tva_id}}`."""

    impl = JSON
    cache_ok = True

    @override
    def process_bind_param(
        self, value: dict[str, RegionSupplier] | None, dialect: Dialect
    ) -> dict[str, dict[str, Any]]:
        return {region: asdict(supplier) for region, supplier in (value or {}).items()}

    @override
    def process_result_value(
        self, value: dict[str, dict[str, Any]] | None, dialect: Dialect
    ) -> dict[str, RegionSupplier]:
        return {region: RegionSupplier(**fields) for region, fields in (value or {}).items()}


metadata = MetaData()
mapper_registry = registry(metadata=metadata)

suppliers = Table(
    "suppliers",
    metadata,
    Column("id", String(), primary_key=True),
    Column("name", String()),
    Column("contact_email", String()),
    Column("contact_phone", String()),
    Column("country", String()),
    Column("region", String()),
)

products = Table(
    "products",
    metadata,
    Column("id", String(), primary_key=True),
    # Héritage mono-table : toutes les variantes partagent la table `products`.
    Column("kind", String(), nullable=False),
    Column("name", String(), nullable=False),
    Column("slug", String(), unique=True, nullable=False),
    Column("images", JSON(), nullable=False),
    Column("expiration_date", Date()),
    Column("shelf_life_days", Integer()),
)

product_pricing = Table(
    "product_pricing",
    metadata,
    Column("product_id", String(), ForeignKey("products.id"), primary_key=True),
    Column("price_base", Float()),
    Column("price_tax", Float()),
    Column("price_tax_rate", Float()),
    Column("discounts", JSON(), nullable=False),
)

product_storage = Table(
    "product_storage",
    metadata,
    Column("product_id", String(), ForeignKey("products.id"), primary_key=True),
    Column("quantity", Integer()),
    Column("stock", Integer()),
    Column("warehouse_location", String()),
)

product_transport = Table(
    "product_transport",
    metadata,
    Column("product_id", String(), ForeignKey("products.id"), primary_key=True),
    Column("kilos", Float()),
    Column("volume", String()),
)

product_supply = Table(
    "product_supply",
    metadata,
    Column("product_id", String(), ForeignKey("products.id"), primary_key=True),
    Column("supplier_id", String(), ForeignKey("suppliers.id")),
    Column("suppliers_regions", _RegionSuppliers(), nullable=False),
)

_PERISHABLE_COLUMNS = ["expiration_date", "shelf_life_days"]

mapper_registry.map_imperatively(Supplier, suppliers)
mapper_registry.map_imperatively(
    Product,
    products,
    polymorphic_on=products.c.kind,
    polymorphic_identity="standard",
    exclude_properties=_PERISHABLE_COLUMNS,
)
mapper_registry.map_imperatively(
    PerishableProduct,
    inherits=Product,
    polymorphic_identity="perishable",
    properties={column: products.c[column] for column in _PERISHABLE_COLUMNS},
)
mapper_registry.map_imperatively(
    NonExpiringProduct, inherits=Product, polymorphic_identity="non_expiring"
)
mapper_registry.map_imperatively(
    ProductPricing,
    product_pricing,
    properties={
        "price": composite(
            Price,
            product_pricing.c.price_base,
            product_pricing.c.price_tax,
            product_pricing.c.price_tax_rate,
        )
    },
)
mapper_registry.map_imperatively(
    ProductStorage,
    product_storage,
    properties={"warehouse": composite(Warehouse, product_storage.c.warehouse_location)},
)
mapper_registry.map_imperatively(ProductTransport, product_transport)
mapper_registry.map_imperatively(ProductSupply, product_supply)
