from omni_product.anemic_model import (
    NonExpiringProduct,
    PerishableProduct,
    Price,
    Product,
    ProductPrice,
    ProductShipment,
    ProductStock,
    ProductSupply,
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
from omni_product.service.product_view import ProductView


def _kind_of(product: Product) -> ProductKind:
    if isinstance(product, PerishableProduct):
        return "perishable"
    if isinstance(product, NonExpiringProduct):
        return "non_expiring"
    return "standard"


def product_to_schema(view: ProductView) -> ProductSchema:
    product = view.product
    perishable = product if isinstance(product, PerishableProduct) else None
    price = view.price
    shipment = view.shipment
    stock = view.stock
    supply = view.supply
    return ProductSchema(
        id=product.id,
        kind=_kind_of(product),
        name=product.name,
        slug=product.slug,
        expiration_date=perishable.expiration_date if perishable else None,
        shelf_life_days=perishable.shelf_life_days if perishable else None,
        price=PriceSchema.model_validate(price.price if price else Price()),
        discounts=list(price.discounts) if price else [],
        images=dict(product.images),
        suppliers_regions={
            region: RegionSupplierSchema.model_validate(supplier)
            for region, supplier in (supply.suppliers_regions.items() if supply else [])
        },
        kilos=shipment.kilos if shipment else None,
        volume=shipment.volume if shipment else None,
        quantity=stock.quantity if stock else None,
        stock=stock.stock if stock else None,
        warehouse=WarehouseSchema.model_validate(stock.warehouse if stock else Warehouse()),
        supplier_id=supply.supplier_id if supply else None,
    )


def schema_to_view(schema: ProductSchema, product_id: str) -> ProductView:
    """Construit des agrégats neufs ; `save` les fusionne avec les existants (comme `PUT` en Java)."""
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
    return ProductView(
        product=product,
        price=ProductPrice(
            product_id=product_id,
            price=Price(**schema.price.model_dump()) if schema.price is not None else Price(),
            discounts=schema.discounts or [],
        ),
        shipment=ProductShipment(product_id=product_id, kilos=schema.kilos, volume=schema.volume),
        stock=ProductStock(
            product_id=product_id,
            quantity=schema.quantity if schema.quantity is not None else schema.stock,
            stock=schema.stock or 0,
            warehouse=(
                Warehouse(**schema.warehouse.model_dump()) if schema.warehouse is not None else Warehouse()
            ),
        ),
        supply=ProductSupply(
            product_id=product_id,
            supplier_id=schema.supplier_id,
            suppliers_regions={
                region: RegionSupplier(**supplier.model_dump())
                for region, supplier in (schema.suppliers_regions or {}).items()
            },
        ),
    )


def supplier_to_schema(supplier: Supplier) -> SupplierSchema:
    return SupplierSchema.model_validate(supplier)
