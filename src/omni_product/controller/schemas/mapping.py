from collections.abc import Mapping, Sequence

from omni_product.controller.schemas.product import (
    PriceSchema,
    ProductKind,
    ProductSchema,
    RegionSupplierSchema,
    WarehouseSchema,
)
from omni_product.controller.schemas.supplier import SupplierSchema
from omni_product.domain.model.pricing import BasePrice, Price, ProductPrice, TaxAmount, TaxRate
from omni_product.domain.model.product import (
    NonExpiringProduct,
    PerishableProduct,
    Product,
    ProductId,
    ShelfLifeDays,
    Slug,
)
from omni_product.domain.model.shipment import Kilos, ProductShipment, Volume
from omni_product.domain.model.stock import (
    ProductStock,
    Quantity,
    Stock,
    Warehouse,
    WarehouseLocation,
)
from omni_product.domain.model.supplier import Supplier
from omni_product.domain.model.supplier_region import RegionSupplier, Siren, TvaId
from omni_product.domain.model.value import raw, wrap


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
        id=product.id.value,
        kind=_kind_of(product),
        name=product.name,
        slug=product.slug.value,
        expiration_date=perishable.expiration_date if perishable else None,
        shelf_life_days=raw(perishable.shelf_life_days) if perishable else None,
        price=_price_to_schema(price.price) if price and price.price else None,
        discounts=list(discounts),
        images=dict(product.images),
        suppliers_regions={
            region: _region_to_schema(supplier)
            for region, supplier in (suppliers_regions or {}).items()
        },
        kilos=raw(shipment.kilos) if shipment else None,
        volume=raw(shipment.volume) if shipment else None,
        quantity=raw(stock.quantity) if stock else None,
        stock=raw(stock.stock) if stock else None,
        warehouse=_warehouse_to_schema(stock.warehouse) if stock and stock.warehouse else None,
        supplier_id=product.supplier_id,
    )


def _price_to_schema(price: Price) -> PriceSchema:
    return PriceSchema(base=raw(price.base), tax=raw(price.tax), tax_rate=raw(price.tax_rate))


def _region_to_schema(supplier: RegionSupplier) -> RegionSupplierSchema:
    return RegionSupplierSchema(
        name=supplier.name, siren=raw(supplier.siren), tva_id=raw(supplier.tva_id)
    )


def _warehouse_to_schema(warehouse: Warehouse) -> WarehouseSchema:
    return WarehouseSchema(location=raw(warehouse.location))


def schema_to_product(schema: ProductSchema, product_id: str) -> Product:
    """Construit une entité neuve ; `save` la fusionne avec l'existante (comme `PUT` en Java)."""
    if schema.name is None or schema.slug is None:
        # La base refuse déjà un nom ou un slug absent : on le dit avant d'arriver au modèle.
        raise ValueError("Product name and slug are required")
    id_ = ProductId(product_id)
    slug = Slug(schema.slug)
    match schema.kind:
        case "perishable":
            product = PerishableProduct(
                id=id_,
                name=schema.name,
                slug=slug,
                expiration_date=schema.expiration_date,
                shelf_life_days=wrap(ShelfLifeDays, schema.shelf_life_days),
            )
        case "non_expiring":
            product = NonExpiringProduct(id=id_, name=schema.name, slug=slug)
        case _:
            product = Product(id=id_, name=schema.name, slug=slug)
    product.supplier_id = schema.supplier_id
    product.images = schema.images or {}
    return product


def schema_to_stock(schema: ProductSchema, product_id: str) -> ProductStock:
    return ProductStock(
        id=ProductId(product_id),
        quantity=wrap(Quantity, schema.quantity if schema.quantity is not None else schema.stock),
        stock=Stock(schema.stock or 0),
        warehouse=_warehouse_from_schema(schema.warehouse)
        if schema.warehouse is not None
        else None,
    )


def _warehouse_from_schema(schema: WarehouseSchema) -> Warehouse:
    return Warehouse(location=wrap(WarehouseLocation, schema.location))


def schema_to_shipment(schema: ProductSchema, product_id: str) -> ProductShipment:
    return ProductShipment(
        id=ProductId(product_id),
        kilos=wrap(Kilos, schema.kilos),
        volume=wrap(Volume, schema.volume),
    )


def schema_to_price(schema: ProductSchema, product_id: str) -> ProductPrice:
    price = _price_from_schema(schema.price) if schema.price is not None else None
    return ProductPrice(id=ProductId(product_id), price=price)


def _price_from_schema(schema: PriceSchema) -> Price:
    return Price(
        base=wrap(BasePrice, schema.base),
        tax=wrap(TaxAmount, schema.tax),
        tax_rate=wrap(TaxRate, schema.tax_rate),
    )


def schema_to_regions(schema: ProductSchema) -> dict[str, RegionSupplier]:
    return {
        region: RegionSupplier(
            name=supplier.name,
            siren=wrap(Siren, supplier.siren),
            tva_id=wrap(TvaId, supplier.tva_id),
        )
        for region, supplier in (schema.suppliers_regions or {}).items()
    }


def supplier_to_schema(supplier: Supplier) -> SupplierSchema:
    return SupplierSchema(
        id=supplier.id.value,
        name=supplier.name,
        contact_email=raw(supplier.contact_email),
        contact_phone=raw(supplier.contact_phone),
        country=raw(supplier.country),
        region=raw(supplier.region),
    )
