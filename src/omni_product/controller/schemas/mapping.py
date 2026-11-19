from collections.abc import Callable
from typing import Protocol

from omni_product.controller.schemas.product import (
    PriceSchema,
    ProductKind,
    ProductSchema,
    RegionSupplierSchema,
    WarehouseSchema,
)
from omni_product.controller.schemas.supplier import SupplierSchema
from omni_product.dal.product_dal import ProductContext
from omni_product.domain.model import (
    Amount,
    Location,
    NonExpiringProduct,
    PerishableProduct,
    Price,
    Product,
    ProductId,
    ProductPricing,
    ProductStorage,
    ProductSupply,
    ProductTransport,
    Quantity,
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


def _optional[P, V](wrap: Callable[[P], V], value: P | None) -> V | None:
    """Les primitives du contrat HTTP deviennent des Value Objects, `None` reste `None`."""
    return None if value is None else wrap(value)


def _primitive[P](value: _HasValue[P] | None) -> P | None:
    return None if value is None else value.value


def _kind_of(product: Product) -> ProductKind:
    if isinstance(product, PerishableProduct):
        return "perishable"
    if isinstance(product, NonExpiringProduct):
        return "non_expiring"
    return "standard"


def product_to_schema(
    product: Product,
    pricing: ProductPricing,
    storage: ProductStorage,
    transport: ProductTransport,
    supply: ProductSupply,
) -> ProductSchema:
    """La réponse HTTP est le seul endroit où les contextes du produit se rejoignent."""
    perishable = product if isinstance(product, PerishableProduct) else None
    return ProductSchema(
        id=product.id.value,
        kind=_kind_of(product),
        name=product.name,
        slug=product.slug.value,
        expiration_date=perishable.expiration_date if perishable else None,
        shelf_life_days=_primitive(perishable.shelf_life_days) if perishable else None,
        price=_price_schema_of(pricing.price) if pricing.price else None,
        discounts=list(pricing.discounts),
        images=dict(product.images),
        suppliers_regions={
            region: _region_supplier_schema_of(supplier)
            for region, supplier in supply.suppliers_regions.items()
        },
        kilos=_primitive(transport.kilos),
        volume=_primitive(transport.volume),
        quantity=_primitive(storage.quantity),
        stock=_primitive(storage.stock),
        warehouse=(
            WarehouseSchema(location=_primitive(storage.warehouse.location))
            if storage.warehouse
            else None
        ),
        supplier_id=_primitive(supply.supplier_id),
    )


def _price_schema_of(price: Price) -> PriceSchema:
    return PriceSchema(
        base=_primitive(price.base),
        tax=_primitive(price.tax),
        tax_rate=_primitive(price.tax_rate),
    )


def _region_supplier_schema_of(supplier: RegionSupplier) -> RegionSupplierSchema:
    return RegionSupplierSchema(
        name=supplier.name,
        siren=_primitive(supplier.siren),
        tva_id=_primitive(supplier.tva_id),
    )


def _region_supplier_of(schema: RegionSupplierSchema) -> RegionSupplier:
    return RegionSupplier(
        name=schema.name,
        siren=_optional(Siren, schema.siren),
        tva_id=_optional(TvaId, schema.tva_id),
    )


def schema_to_product(schema: ProductSchema, product_id: ProductId) -> Product:
    """Construit une entité neuve ; l'enregistrement la fusionne avec l'existante (`PUT`)."""
    return _product_of(schema, product_id)


def schema_to_contexts(schema: ProductSchema, product_id: ProductId) -> list[ProductContext]:
    """Ce que chaque contexte retient du corps de la requête, relié au produit par son id."""
    return [
        _pricing_of(schema, product_id),
        _storage_of(schema, product_id),
        ProductTransport(
            id=product_id,
            kilos=_optional(Weight, schema.kilos),
            volume=_optional(Volume, schema.volume),
        ),
        ProductSupply(
            id=product_id,
            supplier_id=_optional(SupplierId, schema.supplier_id),
            suppliers_regions={
                region: _region_supplier_of(supplier)
                for region, supplier in (schema.suppliers_regions or {}).items()
            },
        ),
    ]


def _product_of(schema: ProductSchema, product_id: ProductId) -> Product:
    slug = Slug(schema.slug)
    match schema.kind:
        case "perishable":
            product = PerishableProduct(
                id=product_id,
                name=schema.name,
                slug=slug,
                expiration_date=schema.expiration_date,
                shelf_life_days=_optional(ShelfLifeDays, schema.shelf_life_days),
            )
        case "non_expiring":
            product = NonExpiringProduct(id=product_id, name=schema.name, slug=slug)
        case _:
            product = Product(id=product_id, name=schema.name, slug=slug)
    product.images = schema.images or {}
    return product


def _pricing_of(schema: ProductSchema, product_id: ProductId) -> ProductPricing:
    pricing = ProductPricing(id=product_id, discounts=schema.discounts or [])
    if schema.price is not None:
        pricing.price = Price(
            base=_optional(Amount, schema.price.base),
            tax=_optional(Amount, schema.price.tax),
            tax_rate=_optional(TaxRate, schema.price.tax_rate),
        )
    return pricing


def _storage_of(schema: ProductSchema, product_id: ProductId) -> ProductStorage:
    storage = ProductStorage(
        id=product_id,
        quantity=_optional(
            Quantity, schema.quantity if schema.quantity is not None else schema.stock
        ),
        stock=Quantity(schema.stock or 0),
    )
    if schema.warehouse is not None:
        storage.warehouse = Warehouse(location=_optional(Location, schema.warehouse.location))
    return storage


def supplier_to_schema(supplier: Supplier) -> SupplierSchema:
    return SupplierSchema(
        id=supplier.id.value,
        name=supplier.name,
        contact_email=_primitive(supplier.contact_email),
        contact_phone=_primitive(supplier.contact_phone),
        country=_primitive(supplier.country),
        region=_primitive(supplier.region),
    )
