from typing import Protocol

from omni_product.controller.schemas.product import (
    PriceSchema,
    ProductKind,
    ProductSchema,
    RegionSupplierSchema,
    WarehouseSchema,
)
from omni_product.controller.schemas.supplier import SupplierSchema
from omni_product.dal.product_dal import ProductRows
from omni_product.domain.model.product import (
    NonExpiringProduct,
    PerishableProduct,
    Price,
    Product,
    ProductDiscount,
    ProductPricing,
    ProductSourcing,
    ProductStorage,
    ProductSupplierRegion,
    ProductTransport,
    RegionSupplier,
    Warehouse,
)
from omni_product.domain.model.product_values import (
    Amount,
    Discount,
    ExpirationDate,
    ImageDetail,
    ImageKey,
    Kilos,
    ProductId,
    ProductName,
    Quantity,
    Region,
    ShelfLifeDays,
    Siren,
    Slug,
    Stock,
    SupplierId,
    SupplierName,
    TaxRate,
    TvaId,
    Volume,
    WarehouseLocation,
)
from omni_product.domain.model.supplier import Supplier


def _kind_of(product: Product) -> ProductKind:
    if isinstance(product, PerishableProduct):
        return "perishable"
    if isinstance(product, NonExpiringProduct):
        return "non_expiring"
    return "standard"


class _Wrapped[T](Protocol):
    @property
    def value(self) -> T: ...


def _value[T](wrapped: _Wrapped[T] | None) -> T | None:
    return None if wrapped is None else wrapped.value


def product_to_schema(rows: ProductRows) -> ProductSchema:
    product, pricing, storage, transport, sourcing, discounts, regions = rows
    perishable = product if isinstance(product, PerishableProduct) else None
    price = pricing.price
    warehouse = storage.warehouse
    return ProductSchema(
        id=product.id.value,
        kind=_kind_of(product),
        name=_value(product.name),
        slug=_value(product.slug),
        expiration_date=(
            perishable.expiration_date.value if perishable and perishable.expiration_date else None
        ),
        shelf_life_days=(
            perishable.shelf_life_days.value if perishable and perishable.shelf_life_days else None
        ),
        price=(
            PriceSchema(
                base=_value(price.base),
                tax=_value(price.tax),
                tax_rate=_value(price.tax_rate),
            )
            if price
            else None
        ),
        discounts=[row.discount.value for row in discounts],
        images={key.value: _value(detail) for key, detail in product.images.items()},
        suppliers_regions={
            row.region.value: RegionSupplierSchema(
                name=_value(row.supplier.name),
                siren=_value(row.supplier.siren),
                tva_id=_value(row.supplier.tva_id),
            )
            for row in regions
        },
        kilos=_value(transport.kilos),
        volume=_value(transport.volume),
        quantity=_value(storage.quantity),
        stock=_value(storage.stock),
        warehouse=(WarehouseSchema(location=_value(warehouse.location)) if warehouse else None),
        supplier_id=_value(sourcing.supplier_id),
    )


def schema_to_product(schema: ProductSchema, product_id: str) -> ProductRows:
    """Construit des lignes neuves ; `save` remplace les anciennes (comme `PUT` en Java)."""
    pid = ProductId(product_id)
    name = None if schema.name is None else ProductName(schema.name)
    slug = None if schema.slug is None else Slug(schema.slug)
    match schema.kind:
        case "perishable":
            product: Product = PerishableProduct(
                id=pid,
                name=name,
                slug=slug,
                expiration_date=(
                    None
                    if schema.expiration_date is None
                    else ExpirationDate(schema.expiration_date)
                ),
                shelf_life_days=(
                    None
                    if schema.shelf_life_days is None
                    else ShelfLifeDays(schema.shelf_life_days)
                ),
            )
        case "non_expiring":
            product = NonExpiringProduct(id=pid, name=name, slug=slug)
        case _:
            product = Product(id=pid, name=name, slug=slug)
    product.images = {
        ImageKey(key): None if detail is None else ImageDetail(detail)
        for key, detail in (schema.images or {}).items()
    }

    supplier_id = None if schema.supplier_id is None else SupplierId(schema.supplier_id)
    quantity = schema.quantity if schema.quantity is not None else schema.stock
    pricing_price = (
        None
        if schema.price is None
        else Price(
            base=None if schema.price.base is None else Amount(schema.price.base),
            tax=None if schema.price.tax is None else Amount(schema.price.tax),
            tax_rate=None if schema.price.tax_rate is None else TaxRate(schema.price.tax_rate),
        )
    )
    warehouse = (
        None
        if schema.warehouse is None
        else Warehouse(
            location=None
            if schema.warehouse.location is None
            else WarehouseLocation(schema.warehouse.location)
        )
    )
    pricing = ProductPricing(id=pid, price=pricing_price)
    storage = ProductStorage(
        id=pid,
        quantity=None if quantity is None else Quantity(quantity),
        stock=Stock(schema.stock or 0),
        warehouse=warehouse,
    )
    transport = ProductTransport(
        id=pid,
        kilos=None if schema.kilos is None else Kilos(schema.kilos),
        volume=None if schema.volume is None else Volume(schema.volume),
    )
    sourcing = ProductSourcing(id=pid, supplier_id=supplier_id)
    discounts = [
        ProductDiscount(id=None, product_id=pid, discount=Discount(discount))
        for discount in schema.discounts or []
    ]
    regions = [
        ProductSupplierRegion(
            id=None,
            product_id=pid,
            region=Region(region),
            supplier=RegionSupplier(
                name=None if supplier.name is None else SupplierName(supplier.name),
                siren=None if supplier.siren is None else Siren(supplier.siren),
                tva_id=None if supplier.tva_id is None else TvaId(supplier.tva_id),
            ),
        )
        for region, supplier in (schema.suppliers_regions or {}).items()
    ]
    return (product, pricing, storage, transport, sourcing, discounts, regions)


def supplier_to_schema(supplier: Supplier) -> SupplierSchema:
    return SupplierSchema(
        id=supplier.id.value,
        name=_value(supplier.name),
        contact_email=_value(supplier.contact_email),
        contact_phone=_value(supplier.contact_phone),
        country=_value(supplier.country),
        region=_value(supplier.region),
    )
