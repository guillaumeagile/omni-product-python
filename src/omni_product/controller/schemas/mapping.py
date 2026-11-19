from omni_product.anemic_model import (
    NonExpiringProduct,
    PerishableProduct,
    Price,
    Product,
    ProductDiscount,
    ProductSupplierRegion,
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
from omni_product.dal.product_dal import ProductRows, empty_rows


def _kind_of(product: Product) -> ProductKind:
    if isinstance(product, PerishableProduct):
        return "perishable"
    if isinstance(product, NonExpiringProduct):
        return "non_expiring"
    return "standard"


def product_to_schema(rows: ProductRows) -> ProductSchema:
    product, pricing, storage, transport, sourcing, discounts, regions = rows
    perishable = product if isinstance(product, PerishableProduct) else None
    return ProductSchema(
        id=product.id,
        kind=_kind_of(product),
        name=product.name,
        slug=product.slug,
        expiration_date=perishable.expiration_date if perishable else None,
        shelf_life_days=perishable.shelf_life_days if perishable else None,
        price=PriceSchema.model_validate(pricing.price) if pricing.price else None,
        discounts=[row.discount for row in discounts],
        images=dict(product.images),
        suppliers_regions={
            row.region: RegionSupplierSchema.model_validate(row.supplier) for row in regions
        },
        kilos=transport.kilos,
        volume=transport.volume,
        quantity=storage.quantity,
        stock=storage.stock,
        warehouse=WarehouseSchema.model_validate(storage.warehouse) if storage.warehouse else None,
        supplier_id=sourcing.supplier_id,
    )


def schema_to_product(schema: ProductSchema, product_id: str) -> ProductRows:
    """Construit des lignes neuves ; `save` les fusionne avec les existantes (comme `PUT`)."""
    match schema.kind:
        case "perishable":
            product: Product = PerishableProduct(
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

    _, pricing, storage, transport, sourcing, _, _ = empty_rows(product, schema.supplier_id)
    transport.kilos = schema.kilos
    transport.volume = schema.volume
    storage.quantity = schema.quantity if schema.quantity is not None else schema.stock
    storage.stock = schema.stock or 0
    if schema.price is not None:
        pricing.price = Price(**schema.price.model_dump())
    if schema.warehouse is not None:
        storage.warehouse = Warehouse(**schema.warehouse.model_dump())
    discounts = [
        ProductDiscount(product_id=product_id, discount=discount)
        for discount in schema.discounts or []
    ]
    regions = [
        ProductSupplierRegion(
            product_id=product_id,
            region=region,
            supplier=RegionSupplier(**supplier.model_dump()),
        )
        for region, supplier in (schema.suppliers_regions or {}).items()
    ]
    return (product, pricing, storage, transport, sourcing, discounts, regions)


def supplier_to_schema(supplier: Supplier) -> SupplierSchema:
    return SupplierSchema.model_validate(supplier)
