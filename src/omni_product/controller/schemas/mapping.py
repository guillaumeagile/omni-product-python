from collections.abc import Callable
from datetime import date
from typing import Protocol

from omni_product.controller.schemas.product import (
    PriceSchema,
    ProductKind,
    ProductSchema,
    RegionSupplierSchema,
    WarehouseSchema,
)
from omni_product.controller.schemas.supplier import SupplierSchema
from omni_product.domain.model.pricing import Amount, Price, TaxRate
from omni_product.domain.model.product import (
    NonExpiring,
    Perishable,
    Product,
    ProductId,
    ShelfLife,
    ShelfLifeDays,
    Slug,
)
from omni_product.domain.model.storage import Location, Warehouse
from omni_product.domain.model.supplier import RegionSupplier, Siren, Supplier, SupplierId, TvaId
from omni_product.service.product_service import ProductDetails


class _Wrapper[T](Protocol):
    """Un Value Object à un champ `value`."""

    @property
    def value(self) -> T: ...


def wrap_optional[T, V](wrap: Callable[[T], V], raw: T | None) -> V | None:
    """Une valeur brute du contrat HTTP devient un Value Object, l'absence reste une absence."""
    return wrap(raw) if raw is not None else None


def _unwrap[T](wrapper: _Wrapper[T] | None) -> T | None:
    return wrapper.value if wrapper is not None else None


def _kind_of(shelf_life: ShelfLife | None) -> ProductKind:
    match shelf_life:
        case Perishable():
            return "perishable"
        case NonExpiring():
            return "non_expiring"
        case None:
            return "standard"


def _perishable_fields(shelf_life: ShelfLife | None) -> tuple[date | None, int | None]:
    match shelf_life:
        case Perishable(expiration_date=expiration_date, shelf_life_days=shelf_life_days):
            return expiration_date, _unwrap(shelf_life_days)
        case NonExpiring() | None:
            return None, None


def _shelf_life_of(schema: ProductSchema) -> ShelfLife | None:
    match schema.kind:
        case "perishable":
            return Perishable(
                expiration_date=schema.expiration_date,
                shelf_life_days=wrap_optional(ShelfLifeDays, schema.shelf_life_days),
            )
        case "non_expiring":
            return NonExpiring()
        case _:
            return None


def _price_schema(price: Price) -> PriceSchema:
    return PriceSchema(
        base=_unwrap(price.base), tax=_unwrap(price.tax), tax_rate=_unwrap(price.tax_rate)
    )


def _region_supplier_schema(supplier: RegionSupplier) -> RegionSupplierSchema:
    return RegionSupplierSchema(
        name=supplier.name, siren=_unwrap(supplier.siren), tva_id=_unwrap(supplier.tva_id)
    )


def _warehouse_schema(warehouse: Warehouse) -> WarehouseSchema:
    return WarehouseSchema(location=_unwrap(warehouse.location))


def product_to_schema(product: Product, details: ProductDetails) -> ProductSchema:
    expiration_date, shelf_life_days = _perishable_fields(product.shelf_life)
    return ProductSchema(
        id=product.id.value,
        kind=_kind_of(product.shelf_life),
        name=product.name,
        slug=product.slug.value,
        expiration_date=expiration_date,
        shelf_life_days=shelf_life_days,
        price=_price_schema(details.price) if details.price is not None else None,
        discounts=list(details.discounts),
        images=dict(details.images),
        suppliers_regions={
            region: _region_supplier_schema(supplier)
            for region, supplier in details.suppliers_regions.items()
        },
        kilos=details.kilos,
        volume=details.volume,
        quantity=details.quantity,
        stock=details.stock,
        warehouse=(_warehouse_schema(details.warehouse) if details.warehouse is not None else None),
        supplier_id=_unwrap(product.supplier_id),
    )


def schema_to_product(schema: ProductSchema, product_id: ProductId) -> Product:
    """Construit l'entité Catalog ; les autres contextes passent par `schema_to_details`."""
    return Product(
        id=product_id,
        name=schema.name,
        slug=Slug(schema.slug),
        supplier_id=wrap_optional(SupplierId, schema.supplier_id),
        shelf_life=_shelf_life_of(schema),
    )


def _price_of(schema: PriceSchema) -> Price:
    return Price(
        base=wrap_optional(Amount, schema.base),
        tax=wrap_optional(Amount, schema.tax),
        tax_rate=wrap_optional(TaxRate, schema.tax_rate),
    )


def _region_supplier_of(schema: RegionSupplierSchema) -> RegionSupplier:
    return RegionSupplier(
        name=schema.name,
        siren=wrap_optional(Siren, schema.siren),
        tva_id=wrap_optional(TvaId, schema.tva_id),
    )


def schema_to_details(schema: ProductSchema) -> ProductDetails:
    return ProductDetails(
        price=_price_of(schema.price) if schema.price is not None else None,
        discounts=schema.discounts or [],
        images=schema.images or {},
        suppliers_regions={
            region: _region_supplier_of(supplier)
            for region, supplier in (schema.suppliers_regions or {}).items()
        },
        kilos=schema.kilos,
        volume=schema.volume,
        quantity=schema.quantity if schema.quantity is not None else schema.stock,
        stock=schema.stock or 0,
        warehouse=(
            Warehouse(location=wrap_optional(Location, schema.warehouse.location))
            if schema.warehouse is not None
            else None
        ),
    )


def supplier_to_schema(supplier: Supplier) -> SupplierSchema:
    return SupplierSchema(
        id=supplier.id.value,
        name=supplier.name,
        contact_email=_unwrap(supplier.contact_email),
        contact_phone=_unwrap(supplier.contact_phone),
        country=_unwrap(supplier.country),
        region=_unwrap(supplier.region),
    )
