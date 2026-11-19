from omni_product.controller.schemas.product import (
    PriceSchema,
    ProductKind,
    ProductSchema,
    RegionSupplierSchema,
    WarehouseSchema,
)
from omni_product.controller.schemas.supplier import SupplierSchema
from omni_product.domain.model.product import (
    NonExpiringProduct,
    PerishableProduct,
    Price,
    Product,
    RegionSupplier,
    Warehouse,
)
from omni_product.domain.model.supplier import Supplier
from omni_product.service.product_service import ProductDetails


def _kind_of(product: Product) -> ProductKind:
    if isinstance(product, PerishableProduct):
        return "perishable"
    if isinstance(product, NonExpiringProduct):
        return "non_expiring"
    return "standard"


def product_to_schema(product: Product, details: ProductDetails) -> ProductSchema:
    perishable = product if isinstance(product, PerishableProduct) else None
    return ProductSchema(
        id=product.id,
        kind=_kind_of(product),
        name=product.name,
        slug=product.slug,
        expiration_date=perishable.expiration_date if perishable else None,
        shelf_life_days=perishable.shelf_life_days if perishable else None,
        price=PriceSchema.model_validate(details.price) if details.price is not None else None,
        discounts=list(details.discounts),
        images=dict(details.images),
        suppliers_regions={
            region: RegionSupplierSchema.model_validate(supplier)
            for region, supplier in details.suppliers_regions.items()
        },
        kilos=details.kilos,
        volume=details.volume,
        quantity=details.quantity,
        stock=details.stock,
        warehouse=(
            WarehouseSchema.model_validate(details.warehouse)
            if details.warehouse is not None
            else None
        ),
        supplier_id=product.supplier_id,
    )


def schema_to_product(schema: ProductSchema, product_id: str) -> Product:
    """Construit l'entité Catalog ; les autres contextes passent par `schema_to_details`."""
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
    product.supplier_id = schema.supplier_id
    return product


def schema_to_details(schema: ProductSchema) -> ProductDetails:
    return ProductDetails(
        price=Price(**schema.price.model_dump()) if schema.price is not None else None,
        discounts=schema.discounts or [],
        images=schema.images or {},
        suppliers_regions={
            region: RegionSupplier(**supplier.model_dump())
            for region, supplier in (schema.suppliers_regions or {}).items()
        },
        kilos=schema.kilos,
        volume=schema.volume,
        quantity=schema.quantity if schema.quantity is not None else schema.stock,
        stock=schema.stock or 0,
        warehouse=(
            Warehouse(**schema.warehouse.model_dump()) if schema.warehouse is not None else None
        ),
    )


def supplier_to_schema(supplier: Supplier) -> SupplierSchema:
    return SupplierSchema.model_validate(supplier)
