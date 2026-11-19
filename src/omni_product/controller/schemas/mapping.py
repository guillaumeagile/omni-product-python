from omni_product.anemic_model import (
    NonExpiringProduct,
    PerishableProduct,
    Price,
    Product,
    ProductAggregate,
    ProductDiscount,
    ProductPricing,
    ProductSourcing,
    ProductStorage,
    ProductSupplierRegion,
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


def _kind_of(product: Product) -> ProductKind:
    if isinstance(product, PerishableProduct):
        return "perishable"
    if isinstance(product, NonExpiringProduct):
        return "non_expiring"
    return "standard"


def product_to_schema(aggregate: ProductAggregate) -> ProductSchema:
    product = aggregate.product
    pricing: ProductPricing = aggregate.pricing
    storage: ProductStorage = aggregate.storage
    transport: ProductTransport = aggregate.transport
    sourcing: ProductSourcing = aggregate.sourcing
    perishable = product if isinstance(product, PerishableProduct) else None
    return ProductSchema(
        id=product.id,
        kind=_kind_of(product),
        name=product.name,
        slug=product.slug,
        expiration_date=perishable.expiration_date if perishable else None,
        shelf_life_days=perishable.shelf_life_days if perishable else None,
        price=PriceSchema.model_validate(pricing.price) if pricing.price else None,
        discounts=[row.discount for row in aggregate.discounts],
        images=dict(product.images),
        suppliers_regions={
            row.region: RegionSupplierSchema.model_validate(row.supplier)
            for row in aggregate.suppliers_regions
        },
        kilos=transport.kilos,
        volume=transport.volume,
        quantity=storage.quantity,
        stock=storage.stock,
        warehouse=WarehouseSchema.model_validate(storage.warehouse) if storage.warehouse else None,
        supplier_id=sourcing.supplier_id,
    )


def schema_to_product(schema: ProductSchema, product_id: str) -> ProductAggregate:
    """Construit un agrégat neuf ; `save` le fusionne avec l'existant (comme `PUT` en Java)."""
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

    aggregate = ProductAggregate.of(product, supplier_id=schema.supplier_id)
    aggregate.transport.kilos = schema.kilos
    aggregate.transport.volume = schema.volume
    aggregate.storage.quantity = schema.quantity if schema.quantity is not None else schema.stock
    aggregate.storage.stock = schema.stock or 0
    if schema.price is not None:
        aggregate.pricing.price = Price(**schema.price.model_dump())
    if schema.warehouse is not None:
        aggregate.storage.warehouse = Warehouse(**schema.warehouse.model_dump())
    aggregate.discounts = [
        ProductDiscount(product_id=product_id, discount=discount)
        for discount in schema.discounts or []
    ]
    aggregate.suppliers_regions = [
        ProductSupplierRegion(
            product_id=product_id,
            region=region,
            supplier=RegionSupplier(**supplier.model_dump()),
        )
        for region, supplier in (schema.suppliers_regions or {}).items()
    ]
    return aggregate


def supplier_to_schema(supplier: Supplier) -> SupplierSchema:
    return SupplierSchema.model_validate(supplier)
