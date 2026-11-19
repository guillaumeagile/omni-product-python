from collections.abc import Mapping, Sequence

from omni_product.anemic_model import (
    NonExpiringProduct,
    PerishableProduct,
    Price,
    Product,
    ProductPrice,
    ProductShipment,
    ProductStock,
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


def product_to_schema(
    product: Product,
    stock: ProductStock | None = None,
    shipment: ProductShipment | None = None,
    price: ProductPrice | None = None,
    discounts: Sequence[str] = (),
    suppliers_regions: Mapping[str, RegionSupplier] | None = None,
) -> ProductSchema:
    perishable = product if isinstance(product, PerishableProduct) else None
    return ProductSchema(
        id=product.id,
        kind=_kind_of(product),
        name=product.name,
        slug=product.slug,
        expiration_date=perishable.expiration_date if perishable else None,
        shelf_life_days=perishable.shelf_life_days if perishable else None,
        price=PriceSchema.model_validate(price.price) if price and price.price else None,
        discounts=list(discounts),
        images=dict(product.images),
        suppliers_regions={
            region: RegionSupplierSchema.model_validate(supplier)
            for region, supplier in (suppliers_regions or {}).items()
        },
        kilos=shipment.kilos if shipment else None,
        volume=shipment.volume if shipment else None,
        quantity=stock.quantity if stock else None,
        stock=stock.stock if stock else None,
        warehouse=WarehouseSchema.model_validate(stock.warehouse)
        if stock and stock.warehouse
        else None,
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
    product.supplier_id = schema.supplier_id
    product.images = schema.images or {}
    return product


def schema_to_stock(schema: ProductSchema, product_id: str) -> ProductStock:
    return ProductStock(
        product_id=product_id,
        quantity=schema.quantity if schema.quantity is not None else schema.stock,
        stock=schema.stock or 0,
        warehouse=Warehouse(**schema.warehouse.model_dump())
        if schema.warehouse is not None
        else None,
    )


def schema_to_shipment(schema: ProductSchema, product_id: str) -> ProductShipment:
    return ProductShipment(product_id=product_id, kilos=schema.kilos, volume=schema.volume)


def schema_to_price(schema: ProductSchema, product_id: str) -> ProductPrice:
    price = Price(**schema.price.model_dump()) if schema.price is not None else None
    return ProductPrice(product_id=product_id, price=price)


def schema_to_regions(schema: ProductSchema) -> dict[str, RegionSupplier]:
    return {
        region: RegionSupplier(**supplier.model_dump())
        for region, supplier in (schema.suppliers_regions or {}).items()
    }


def supplier_to_schema(supplier: Supplier) -> SupplierSchema:
    return SupplierSchema.model_validate(supplier)
