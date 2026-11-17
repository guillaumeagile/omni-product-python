from omni_product.controller.schemas.product import (
    PriceSchema,
    ProductKind,
    ProductSchema,
    RegionSupplierSchema,
    WarehouseSchema,
)
from omni_product.controller.schemas.supplier import SupplierSchema
from omni_product.dal.product_dal import ProductSheet
from omni_product.dal.records import optional, raw
from omni_product.domain.model import (
    Amount,
    Discount,
    ImageDetail,
    ImageKey,
    Kilos,
    Location,
    NonExpiring,
    Perishable,
    Price,
    Product,
    ProductId,
    ProductImage,
    ProductPrice,
    ProductStock,
    ProductSupply,
    ProductTransport,
    Quantity,
    Rate,
    Region,
    RegionSupplier,
    ShelfLife,
    ShelfLifeDays,
    Siren,
    Slug,
    Stock,
    Supplier,
    SupplierByRegion,
    SupplierId,
    TvaId,
    Volume,
    Warehouse,
)
from omni_product.exception.product_name_exception import ProductNameException


def _kind_of(product: Product) -> ProductKind:
    match product.shelf_life:
        case Perishable():
            return "perishable"
        case NonExpiring():
            return "non_expiring"
        case None:
            return "standard"


def product_to_schema(sheet: ProductSheet) -> ProductSchema:
    product = sheet.product
    perishable = product.shelf_life if isinstance(product.shelf_life, Perishable) else None
    pricing = sheet.pricing
    price = pricing.price if pricing is not None else None
    transport = sheet.transport
    stock = sheet.stock
    supply = sheet.supply
    return ProductSchema(
        id=product.id.value,
        kind=_kind_of(product),
        name=product.name,
        slug=product.slug.value,
        expiration_date=perishable.expiration_date if perishable else None,
        shelf_life_days=raw(perishable.shelf_life_days) if perishable else None,
        price=(
            PriceSchema(base=raw(price.base), tax=raw(price.tax), tax_rate=raw(price.tax_rate))
            if price is not None
            else None
        ),
        discounts=[discount.value for discount in pricing.discounts] if pricing else [],
        images={image.key.value: raw(image.detail) for image in product.images},
        suppliers_regions=(
            {
                line.region.value: RegionSupplierSchema(
                    name=line.supplier.name,
                    siren=raw(line.supplier.siren),
                    tva_id=raw(line.supplier.tva_id),
                )
                for line in supply.regions
            }
            if supply is not None
            else {}
        ),
        kilos=raw(transport.kilos) if transport is not None else None,
        volume=raw(transport.volume) if transport is not None else None,
        quantity=raw(stock.quantity) if stock is not None else None,
        stock=raw(stock.stock) if stock is not None else None,
        warehouse=(
            WarehouseSchema(location=raw(stock.warehouse.location))
            if stock is not None and stock.warehouse is not None
            else None
        ),
        supplier_id=raw(supply.supplier_id) if supply is not None else None,
    )


def schema_to_product(schema: ProductSchema, product_id: str) -> ProductSheet:
    """Construit une fiche neuve ; `save` la fusionne avec l'existante (comme `PUT` en Java)."""
    pid = ProductId(product_id)
    # Un produit doit avoir un nom et un slug : sans eux, la base refusait l'écriture.
    if schema.name is None:
        raise ProductNameException("Product name is missing")
    if schema.slug is None:
        raise ValueError("Product slug is missing")
    name = schema.name
    slug = Slug(schema.slug)
    images = tuple(
        ProductImage(key=ImageKey(key), detail=optional(ImageDetail, detail))
        for key, detail in (schema.images or {}).items()
    )
    match schema.kind:
        case "perishable":
            shelf_life: ShelfLife | None = Perishable(
                expiration_date=schema.expiration_date,
                shelf_life_days=optional(ShelfLifeDays, schema.shelf_life_days),
            )
        case "non_expiring":
            shelf_life = NonExpiring()
        case _:
            shelf_life = None
    product = Product(id=pid, name=name, slug=slug, images=images, shelf_life=shelf_life)
    price = schema.price
    warehouse = schema.warehouse
    return ProductSheet(
        product=product,
        pricing=ProductPrice(
            id=pid,
            price=(
                Price(
                    base=optional(Amount, price.base),
                    tax=optional(Amount, price.tax),
                    tax_rate=optional(Rate, price.tax_rate),
                )
                if price is not None
                else None
            ),
            discounts=tuple(Discount(value) for value in schema.discounts or []),
        ),
        transport=ProductTransport(
            id=pid,
            kilos=optional(Kilos, schema.kilos),
            volume=optional(Volume, schema.volume),
        ),
        stock=ProductStock(
            id=pid,
            quantity=optional(
                Quantity, schema.quantity if schema.quantity is not None else schema.stock
            ),
            stock=Stock(schema.stock or 0),
            warehouse=(
                Warehouse(location=optional(Location, warehouse.location)) if warehouse else None
            ),
        ),
        supply=ProductSupply(
            id=pid,
            supplier_id=optional(SupplierId, schema.supplier_id),
            regions=tuple(
                SupplierByRegion(
                    region=Region(region),
                    supplier=RegionSupplier(
                        name=supplier.name,
                        siren=optional(Siren, supplier.siren),
                        tva_id=optional(TvaId, supplier.tva_id),
                    ),
                )
                for region, supplier in (schema.suppliers_regions or {}).items()
            ),
        ),
    )


def supplier_to_schema(supplier: Supplier) -> SupplierSchema:
    return SupplierSchema(
        id=supplier.id.value,
        name=supplier.name,
        contact_email=raw(supplier.contact_email),
        contact_phone=raw(supplier.contact_phone),
        country=raw(supplier.country),
        region=raw(supplier.region),
    )
