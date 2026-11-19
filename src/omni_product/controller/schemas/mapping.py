from omni_product.anemic_model import (
    NonExpiringProduct,
    PerishableProduct,
    Price,
    Product,
    ProductPricing,
    ProductStorage,
    ProductSupplierContext,
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
from omni_product.service.product_service import ProductRecord


def _kind_of(product: Product) -> ProductKind:
    if isinstance(product, PerishableProduct):
        return "perishable"
    if isinstance(product, NonExpiringProduct):
        return "non_expiring"
    return "standard"


def product_to_schema(record: ProductRecord) -> ProductSchema:
    product, pricing, storage, transport, supplier = record
    perishable = product if isinstance(product, PerishableProduct) else None
    suppliers_regions = supplier.suppliers_regions if supplier else {}
    return ProductSchema(
        id=product.id,
        kind=_kind_of(product),
        name=product.name,
        slug=product.slug,
        expiration_date=perishable.expiration_date if perishable else None,
        shelf_life_days=perishable.shelf_life_days if perishable else None,
        price=PriceSchema.model_validate(pricing.price) if pricing and pricing.price else None,
        discounts=list(pricing.discounts) if pricing else [],
        images=dict(product.images),
        suppliers_regions={
            region: RegionSupplierSchema.model_validate(supplier)
            for region, supplier in suppliers_regions.items()
        },
        kilos=transport.kilos if transport else None,
        volume=transport.volume if transport else None,
        quantity=storage.quantity if storage else None,
        stock=storage.stock if storage else None,
        warehouse=(
            WarehouseSchema.model_validate(storage.warehouse)
            if storage and storage.warehouse
            else None
        ),
        supplier_id=supplier.supplier_id if supplier else None,
    )


def schema_to_product_record(schema: ProductSchema, product_id: str) -> ProductRecord:
    """Construit les modèles de contexte à persister pour un produit."""
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

    pricing = ProductPricing(product_id=product_id)
    if schema.price is not None:
        pricing.price = Price(**schema.price.model_dump())
    pricing.discounts = schema.discounts or []

    storage = ProductStorage(
        product_id=product_id,
        quantity=schema.quantity if schema.quantity is not None else schema.stock,
        stock=schema.stock or 0,
    )
    if schema.warehouse is not None:
        storage.warehouse = Warehouse(**schema.warehouse.model_dump())

    transport = ProductTransport(
        product_id=product_id,
        kilos=schema.kilos,
        volume=schema.volume,
    )
    supplier = ProductSupplierContext(product_id=product_id, supplier_id=schema.supplier_id)
    product.images = schema.images or {}
    supplier.suppliers_regions = {
        region: RegionSupplier(**supplier.model_dump())
        for region, supplier in (schema.suppliers_regions or {}).items()
    }
    return product, pricing, storage, transport, supplier


def supplier_to_schema(supplier: Supplier) -> SupplierSchema:
    return SupplierSchema.model_validate(supplier)
