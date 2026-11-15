from omni_product.anemic_model import (
    NonExpiringProduct,
    PerishableProduct,
    Price,
    Product,
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
from omni_product.dal.product_dal import ProductSheet


def _kind_of(product: Product) -> ProductKind:
    if isinstance(product, PerishableProduct):
        return "perishable"
    if isinstance(product, NonExpiringProduct):
        return "non_expiring"
    return "standard"


def product_to_schema(sheet: ProductSheet) -> ProductSchema:
    product = sheet.product
    perishable = product if isinstance(product, PerishableProduct) else None
    return ProductSchema(
        id=product.id,
        kind=_kind_of(product),
        name=product.name,
        slug=product.slug,
        expiration_date=perishable.expiration_date if perishable else None,
        shelf_life_days=perishable.shelf_life_days if perishable else None,
        price=PriceSchema.model_validate(sheet.price) if sheet.price else None,
        discounts=list(sheet.discounts),
        images=dict(product.images),
        suppliers_regions={
            region: RegionSupplierSchema.model_validate(supplier)
            for region, supplier in sheet.suppliers_regions.items()
        },
        kilos=sheet.kilos,
        volume=sheet.volume,
        quantity=sheet.quantity,
        stock=sheet.stock,
        warehouse=WarehouseSchema.model_validate(sheet.warehouse) if sheet.warehouse else None,
        supplier_id=sheet.supplier_id,
    )


def schema_to_product(schema: ProductSchema, product_id: str) -> ProductSheet:
    """Construit une fiche neuve ; `save` la fusionne avec l'existante (comme `PUT` en Java)."""
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
    return ProductSheet(
        product=product,
        price=Price(**schema.price.model_dump()) if schema.price is not None else None,
        discounts=schema.discounts or [],
        kilos=schema.kilos,
        volume=schema.volume,
        quantity=schema.quantity if schema.quantity is not None else schema.stock,
        stock=schema.stock or 0,
        warehouse=Warehouse(**schema.warehouse.model_dump()) if schema.warehouse else None,
        supplier_id=schema.supplier_id,
        suppliers_regions={
            region: RegionSupplier(**supplier.model_dump())
            for region, supplier in (schema.suppliers_regions or {}).items()
        },
    )


def supplier_to_schema(supplier: Supplier) -> SupplierSchema:
    return SupplierSchema.model_validate(supplier)
