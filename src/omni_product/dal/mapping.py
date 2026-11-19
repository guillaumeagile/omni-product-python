"""Le branchement du modèle sur la base : tables et mapping impératif SQLAlchemy.

Le modèle (`domain/model/`) ne connaît pas SQLAlchemy. Ce module décrit les tables et y
branche les dataclasses du domaine de l'extérieur, une seule fois, à l'import.
"""

from collections.abc import Callable
from datetime import date
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
    event,
)
from sqlalchemy.orm import Session, composite, registry

from omni_product.domain.model import (
    Amount,
    Country,
    Email,
    Location,
    NonExpiring,
    Perishable,
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
    ShelfLife,
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
    # La conservation (`ShelfLife`) se range à plat : son genre et les champs du périssable.
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

mapper_registry.map_imperatively(Supplier, suppliers)
# Les colonnes de la conservation vivent dans des attributs privés, que le modèle ne déclare pas.
# Les événements plus bas les tiennent d'accord avec `Product.shelf_life`.
mapper_registry.map_imperatively(
    Product,
    products,
    properties={
        "_kind": products.c.kind,
        "_expiration_date": products.c.expiration_date,
        "_shelf_life_days": products.c.shelf_life_days,
    },
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


def _shelf_life_of_columns(
    kind: str, expiration_date: date | None, shelf_life_days: ShelfLifeDays | None
) -> ShelfLife | None:
    match kind:
        case "perishable":
            return Perishable(expiration_date=expiration_date, shelf_life_days=shelf_life_days)
        case "non_expiring":
            return NonExpiring()
        case _:
            return None


def _columns_of_shelf_life(
    shelf_life: ShelfLife | None,
) -> tuple[str, date | None, ShelfLifeDays | None]:
    match shelf_life:
        case Perishable(expiration_date=expiration_date, shelf_life_days=shelf_life_days):
            return "perishable", expiration_date, shelf_life_days
        case NonExpiring():
            return "non_expiring", None, None
        case None:
            return "standard", None, None


# Les attributs privés que le mapping ajoute à `Product`, dans l'ordre des colonnes.
_SHELF_LIFE_ATTRIBUTES = ("_kind", "_expiration_date", "_shelf_life_days")


@event.listens_for(Product, "load")
def _read_shelf_life(product: Product, _: object) -> None:
    kind, expiration_date, shelf_life_days = (
        getattr(product, name) for name in _SHELF_LIFE_ATTRIBUTES
    )
    product.shelf_life = _shelf_life_of_columns(kind, expiration_date, shelf_life_days)


def _products_with_shelf_life(session: Session) -> list[Product]:
    """Les produits de la session ; `merge` en crée sans `shelf_life`, avant de le recopier."""
    products_in_session = [
        instance
        for instance in (*session.new, *session.identity_map.values())
        if isinstance(instance, Product)
    ]
    return [product for product in products_in_session if "shelf_life" in vars(product)]


@event.listens_for(Session, "before_commit")
@event.listens_for(Session, "before_flush")
def _write_shelf_life(session: Session, *_: object) -> None:
    """`shelf_life` n'est pas suivi par la session : on le recopie dans les colonnes.

    Avant le commit aussi : si seul `shelf_life` a changé, la session se croit propre et ne
    lancerait pas de flush.
    """
    for product in _products_with_shelf_life(session):
        columns = _columns_of_shelf_life(product.shelf_life)
        for name, value in zip(_SHELF_LIFE_ATTRIBUTES, columns, strict=True):
            setattr(product, name, value)
