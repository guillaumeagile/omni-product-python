"""Le branchement du modèle sur la base : tables et mapping impératif SQLAlchemy.

Le modèle (`domain/model/`) ne connaît pas SQLAlchemy. Ce module décrit les tables et y
branche les dataclasses du domaine de l'extérieur, une seule fois, à l'import.
"""

from collections.abc import Callable
from typing import Any, Protocol, override

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
    Amount,
    Country,
    Email,
    Location,
    NonExpiringProduct,
    PerishableProduct,
    Phone,
    Price,
    Product,
    ProductId,
    ProductPricing,
    ProductStorage,
    ProductSupply,
    ProductTransport,
    Quantity,
    Region,
    RegionSupplier,
    ShelfLifeDays,
    Siren,
    Slug,
    Supplier,
    SupplierId,
    TaxRate,
    TvaId,
    Volume,
    Warehouse,
    Weight,
)


class _HasValue[P](Protocol):
    @property
    def value(self) -> P: ...


class _Valued[V: _HasValue[Any], P](TypeDecorator[V]):
    """Une colonne primitive (`P`) qui se lit en Value Object (`V`) à un seul champ `value`."""

    cache_ok = True

    def __init__(self, wrap: Callable[[P], V]) -> None:
        super().__init__()
        self.wrap = wrap

    @override
    def process_bind_param(self, value: V | None, dialect: Dialect) -> P | None:
        return None if value is None else value.value

    @override
    def process_result_value(self, value: P | None, dialect: Dialect) -> V | None:
        return None if value is None else self.wrap(value)


class _StringValued[V: _HasValue[str]](_Valued[V, str]):
    impl = String
    cache_ok = True


class _FloatValued[V: _HasValue[float]](_Valued[V, float]):
    impl = Float
    cache_ok = True


class _IntegerValued[V: _HasValue[int]](_Valued[V, int]):
    impl = Integer
    cache_ok = True


def _optional[V](wrap: Callable[[Any], V], value: Any) -> V | None:
    return None if value is None else wrap(value)


def _region_supplier_to_json(supplier: RegionSupplier) -> dict[str, str | None]:
    return {
        "name": supplier.name,
        "siren": supplier.siren.value if supplier.siren else None,
        "tva_id": supplier.tva_id.value if supplier.tva_id else None,
    }


def _region_supplier_of_json(fields: dict[str, str | None]) -> RegionSupplier:
    return RegionSupplier(
        name=fields.get("name"),
        siren=_optional(Siren, fields.get("siren")),
        tva_id=_optional(TvaId, fields.get("tva_id")),
    )


class _RegionSuppliers(TypeDecorator[dict[str, RegionSupplier]]):
    """Les fournisseurs par région, rangés en JSON : `{région: {name, siren, tva_id}}`."""

    impl = JSON
    cache_ok = True

    @override
    def process_bind_param(
        self, value: dict[str, RegionSupplier] | None, dialect: Dialect
    ) -> dict[str, dict[str, str | None]]:
        return {
            region: _region_supplier_to_json(supplier) for region, supplier in (value or {}).items()
        }

    @override
    def process_result_value(
        self, value: dict[str, dict[str, str | None]] | None, dialect: Dialect
    ) -> dict[str, RegionSupplier]:
        return {
            region: _region_supplier_of_json(fields) for region, fields in (value or {}).items()
        }


metadata = MetaData()
mapper_registry = registry(metadata=metadata)

suppliers = Table(
    "suppliers",
    metadata,
    Column("id", _StringValued(SupplierId), primary_key=True),
    Column("name", String()),
    Column("contact_email", _StringValued(Email)),
    Column("contact_phone", _StringValued(Phone)),
    Column("country", _StringValued(Country)),
    Column("region", _StringValued(Region)),
)

products = Table(
    "products",
    metadata,
    Column("id", _StringValued(ProductId), primary_key=True),
    # Héritage mono-table : toutes les variantes partagent la table `products`.
    Column("kind", String(), nullable=False),
    Column("name", String(), nullable=False),
    Column("slug", _StringValued(Slug), unique=True, nullable=False),
    Column("images", JSON(), nullable=False),
    Column("expiration_date", Date()),
    Column("shelf_life_days", _IntegerValued(ShelfLifeDays)),
)

product_pricing = Table(
    "product_pricing",
    metadata,
    Column("product_id", _StringValued(ProductId), ForeignKey("products.id"), primary_key=True),
    Column("price_base", _FloatValued(Amount)),
    Column("price_tax", _FloatValued(Amount)),
    Column("price_tax_rate", _FloatValued(TaxRate)),
    Column("discounts", JSON(), nullable=False),
)

product_storage = Table(
    "product_storage",
    metadata,
    Column("product_id", _StringValued(ProductId), ForeignKey("products.id"), primary_key=True),
    Column("quantity", _IntegerValued(Quantity)),
    Column("stock", _IntegerValued(Quantity)),
    Column("warehouse_location", _StringValued(Location)),
)

product_transport = Table(
    "product_transport",
    metadata,
    Column("product_id", _StringValued(ProductId), ForeignKey("products.id"), primary_key=True),
    Column("kilos", _FloatValued(Weight)),
    Column("volume", _StringValued(Volume)),
)

product_supply = Table(
    "product_supply",
    metadata,
    Column("product_id", _StringValued(ProductId), ForeignKey("products.id"), primary_key=True),
    Column("supplier_id", _StringValued(SupplierId), ForeignKey("suppliers.id")),
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
        "id": product_pricing.c.product_id,
        "price": composite(
            Price,
            product_pricing.c.price_base,
            product_pricing.c.price_tax,
            product_pricing.c.price_tax_rate,
        ),
    },
)
mapper_registry.map_imperatively(
    ProductStorage,
    product_storage,
    properties={
        "id": product_storage.c.product_id,
        "warehouse": composite(Warehouse, product_storage.c.warehouse_location),
    },
)
# Les contextes partagent l'identité du produit : l'attribut `id` lit la colonne `product_id`.
mapper_registry.map_imperatively(
    ProductTransport, product_transport, properties={"id": product_transport.c.product_id}
)
mapper_registry.map_imperatively(
    ProductSupply, product_supply, properties={"id": product_supply.c.product_id}
)
