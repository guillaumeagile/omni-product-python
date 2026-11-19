from omni_product.anemic_model import (
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
from omni_product.controller.schemas.product import (
    PriceSchema,
    ProductKind,
    ProductSchema,
    RegionSupplierSchema,
    WarehouseSchema,
)
from omni_product.controller.schemas.supplier import SupplierSchema
from omni_product.service.product_sheet import ProductSheet


def _kind_of(product: Product) -> ProductKind:
    if isinstance(product, PerishableProduct):
        return "perishable"
    if isinstance(product, NonExpiringProduct):
        return "non_expiring"
    return "standard"


def sheet_to_schema(sheet: ProductSheet) -> ProductSchema:
    product, pricing, storage = sheet.product, sheet.pricing, sheet.storage
    perishable = product if isinstance(product, PerishableProduct) else None
    return ProductSchema(
        id=product.id,
        kind=_kind_of(product),
        name=product.name,
        slug=product.slug,
        expiration_date=perishable.expiration_date if perishable else None,
        shelf_life_days=perishable.shelf_life_days if perishable else None,
        price=PriceSchema.model_validate(pricing.price) if pricing.price else None,
        discounts=list(pricing.discounts),
        images=dict(product.images),
        suppliers_regions={
            region: RegionSupplierSchema.model_validate(supplier)
            for region, supplier in sheet.supply.suppliers_regions.items()
        },
        kilos=sheet.transport.kilos,
        volume=sheet.transport.volume,
        quantity=storage.quantity,
        stock=storage.stock,
        warehouse=WarehouseSchema.model_validate(storage.warehouse) if storage.warehouse else None,
        supplier_id=sheet.supply.supplier_id,
    )


def schema_to_sheet(schema: ProductSchema, product_id: str) -> ProductSheet:
    """Construit des entités neuves ; `save_sheet` les fusionne avec l'existant (`PUT` en Java)."""
    return ProductSheet(
        product=_product_of(schema, product_id),
        pricing=_pricing_of(schema, product_id),
        storage=_storage_of(schema, product_id),
        transport=ProductTransport(product_id=product_id, kilos=schema.kilos, volume=schema.volume),
        supply=ProductSupply(
            product_id=product_id,
            supplier_id=schema.supplier_id,
            suppliers_regions={
                region: RegionSupplier(**supplier.model_dump())
                for region, supplier in (schema.suppliers_regions or {}).items()
            },
        ),
    )


def _product_of(schema: ProductSchema, product_id: str) -> Product:
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
    product.images = schema.images or {}
    return product


def _pricing_of(schema: ProductSchema, product_id: str) -> ProductPricing:
    pricing = ProductPricing(product_id=product_id, discounts=schema.discounts or [])
    if schema.price is not None:
        pricing.price = Price(**schema.price.model_dump())
    return pricing


def _storage_of(schema: ProductSchema, product_id: str) -> ProductStorage:
    storage = ProductStorage(
        product_id=product_id,
        quantity=schema.quantity if schema.quantity is not None else schema.stock,
        stock=schema.stock or 0,
    )
    if schema.warehouse is not None:
        storage.warehouse = Warehouse(**schema.warehouse.model_dump())
    return storage


def supplier_to_schema(supplier: Supplier) -> SupplierSchema:
    return SupplierSchema.model_validate(supplier)
