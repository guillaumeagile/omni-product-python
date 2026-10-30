from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from omni_product.model import (
    NonExpiringProduct,
    PerishableProduct,
    Price,
    Product,
    RegionSupplier,
    Supplier,
    Warehouse,
)


class CamelModel(BaseModel):
    """JSON en camelCase comme Jackson, attributs Python en snake_case."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


class PriceSchema(CamelModel):
    base: float | None = None
    tax: float | None = None
    tax_rate: float | None = None


class WarehouseSchema(CamelModel):
    location: str | None = None


class RegionSupplierSchema(CamelModel):
    name: str | None = None
    siren: str | None = None
    tva_id: str | None = None


ProductKind = Literal["standard", "perishable", "non_expiring"]


class ProductSchema(CamelModel):
    id: str | None = None
    kind: ProductKind | None = None
    name: str | None = None
    slug: str | None = None
    price: PriceSchema | None = None
    discounts: list[str] | None = None
    images: dict[str, str | None] | None = None
    suppliers_regions: dict[str, RegionSupplierSchema] | None = None
    kilos: float | None = None
    volume: str | None = None
    quantity: int | None = None
    stock: int | None = None
    warehouse: WarehouseSchema | None = None
    supplier_id: str | None = None
    # Champs de PerishableProduct, à plat : le client doit savoir lesquels ont un sens pour `kind`.
    expiration_date: date | None = None
    shelf_life_days: int | None = None


class SupplierUpdateRequest(CamelModel):
    name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    country: str | None = None
    region: str | None = None


class SupplierRequest(SupplierUpdateRequest):
    id: str


class SupplierSchema(SupplierRequest):
    """Même forme que la requête de création, pour ne pas recopier les cinq champs."""


def _kind_of(product: Product) -> ProductKind:
    if isinstance(product, PerishableProduct):
        return "perishable"
    if isinstance(product, NonExpiringProduct):
        return "non_expiring"
    return "standard"


def product_to_schema(product: Product) -> ProductSchema:
    perishable = product if isinstance(product, PerishableProduct) else None
    return ProductSchema(
        id=product.id,
        kind=_kind_of(product),
        name=product.name,
        slug=product.slug,
        expiration_date=perishable.expiration_date if perishable else None,
        shelf_life_days=perishable.shelf_life_days if perishable else None,
        price=PriceSchema.model_validate(product.price) if product.price else None,
        discounts=list(product.discounts),
        images=dict(product.images),
        suppliers_regions={
            region: RegionSupplierSchema.model_validate(supplier)
            for region, supplier in product.suppliers_regions.items()
        },
        kilos=product.kilos,
        volume=product.volume,
        quantity=product.quantity,
        stock=product.stock,
        warehouse=WarehouseSchema.model_validate(product.warehouse) if product.warehouse else None,
        supplier_id=product.supplier_id,
    )


def schema_to_product(schema: ProductSchema, product_id: str) -> Product:
    """Construit une entité neuve ; `save` la fusionne avec l'existante (comme `PUT` en Java)."""
    match schema.kind:
        case "perishable":
            product = PerishableProduct(
                id=product_id,
                name=schema.name,
                slug=schema.slug,
                expiration_date=schema.expiration_date,
                shelf_life_days=schema.shelf_life_days,
            )
        case "non_expiring":
            product = NonExpiringProduct(id=product_id, name=schema.name, slug=schema.slug)
        case _:
            product = Product(id=product_id, name=schema.name, slug=schema.slug)
    product.kilos = schema.kilos
    product.volume = schema.volume
    product.quantity = schema.quantity
    product.stock = schema.stock
    product.supplier_id = schema.supplier_id
    if schema.price is not None:
        product.price = Price(**schema.price.model_dump())
    if schema.warehouse is not None:
        product.warehouse = Warehouse(**schema.warehouse.model_dump())
    product.discounts = schema.discounts or []
    product.images = schema.images or {}
    product.suppliers_regions = {
        region: RegionSupplier(**supplier.model_dump())
        for region, supplier in (schema.suppliers_regions or {}).items()
    }
    return product


def supplier_to_schema(supplier: Supplier) -> SupplierSchema:
    return SupplierSchema.model_validate(supplier)
