"""Passage entre les lignes de la base et le modèle métier.

Les DAL s'en servent : le reste de l'application ne voit que le modèle métier.
"""

from collections.abc import Mapping

from omni_product.dal.rows import (
    ProductImageRow,
    ProductPriceRow,
    ProductRow,
    ProductShipmentRow,
    ProductStockRow,
    ProductSupplierRegionRow,
    SupplierRow,
)
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
from omni_product.domain.model.supplier import (
    Country,
    Email,
    Phone,
    Region,
    Supplier,
    SupplierId,
)
from omni_product.domain.model.supplier_region import RegionSupplier, Siren, TvaId
from omni_product.domain.model.value import raw, wrap


def product_from_row(row: ProductRow) -> Product:
    images: dict[str, str | None] = {
        key: image.image_detail for key, image in row.image_rows.items()
    }
    id_ = ProductId(row.id)
    slug = Slug(row.slug)
    match row.kind:
        case "perishable":
            return PerishableProduct(
                id=id_,
                name=row.name,
                slug=slug,
                supplier_id=row.supplier_id,
                images=images,
                expiration_date=row.expiration_date,
                shelf_life_days=wrap(ShelfLifeDays, row.shelf_life_days),
            )
        case "non_expiring":
            return NonExpiringProduct(
                id=id_, name=row.name, slug=slug, supplier_id=row.supplier_id, images=images
            )
        case _:
            return Product(
                id=id_, name=row.name, slug=slug, supplier_id=row.supplier_id, images=images
            )


def product_to_row(product: Product) -> ProductRow:
    perishable = product if isinstance(product, PerishableProduct) else None
    return ProductRow(
        id=product.id.value,
        kind=_kind_of(product),
        name=product.name,
        slug=product.slug.value,
        supplier_id=product.supplier_id,
        expiration_date=perishable.expiration_date if perishable else None,
        shelf_life_days=raw(perishable.shelf_life_days) if perishable else None,
        image_rows={
            key: ProductImageRow(product_id=product.id.value, image_key=key, image_detail=detail)
            for key, detail in product.images.items()
        },
    )


def _kind_of(product: Product) -> str:
    if isinstance(product, PerishableProduct):
        return "perishable"
    if isinstance(product, NonExpiringProduct):
        return "non_expiring"
    return "standard"


def price_from_row(row: ProductPriceRow) -> ProductPrice:
    # Comme le composite d'avant : un prix dont toutes les colonnes sont nulles n'existe pas.
    values = (row.price_base, row.price_tax, row.price_tax_rate)
    price = (
        None
        if all(value is None for value in values)
        else Price(
            base=wrap(BasePrice, row.price_base),
            tax=wrap(TaxAmount, row.price_tax),
            tax_rate=wrap(TaxRate, row.price_tax_rate),
        )
    )
    return ProductPrice(id=ProductId(row.product_id), price=price)


def price_to_row(price: ProductPrice) -> ProductPriceRow:
    value = price.price
    return ProductPriceRow(
        product_id=price.id.value,
        price_base=raw(value.base) if value else None,
        price_tax=raw(value.tax) if value else None,
        price_tax_rate=raw(value.tax_rate) if value else None,
    )


def shipment_from_row(row: ProductShipmentRow) -> ProductShipment:
    return ProductShipment(
        id=ProductId(row.product_id), kilos=wrap(Kilos, row.kilos), volume=wrap(Volume, row.volume)
    )


def shipment_to_row(shipment: ProductShipment) -> ProductShipmentRow:
    return ProductShipmentRow(
        product_id=shipment.id.value,
        kilos=raw(shipment.kilos),
        volume=raw(shipment.volume),
    )


def stock_from_row(row: ProductStockRow) -> ProductStock:
    warehouse = (
        None
        if row.warehouse_location is None
        else Warehouse(location=WarehouseLocation(row.warehouse_location))
    )
    return ProductStock(
        id=ProductId(row.product_id),
        quantity=wrap(Quantity, row.quantity),
        stock=wrap(Stock, row.stock),
        warehouse=warehouse,
    )


def stock_to_row(stock: ProductStock) -> ProductStockRow:
    return ProductStockRow(
        product_id=stock.id.value,
        quantity=raw(stock.quantity),
        stock=raw(stock.stock),
        warehouse_location=raw(stock.warehouse.location) if stock.warehouse else None,
    )


def supplier_from_row(row: SupplierRow) -> Supplier:
    return Supplier(
        id=SupplierId(row.id),
        name=row.name,
        contact_email=wrap(Email, row.contact_email),
        contact_phone=wrap(Phone, row.contact_phone),
        country=wrap(Country, row.country),
        region=wrap(Region, row.region),
    )


def supplier_to_row(supplier: Supplier) -> SupplierRow:
    return SupplierRow(
        id=supplier.id.value,
        name=supplier.name,
        contact_email=raw(supplier.contact_email),
        contact_phone=raw(supplier.contact_phone),
        country=raw(supplier.country),
        region=raw(supplier.region),
    )


def region_from_row(row: ProductSupplierRegionRow) -> RegionSupplier:
    return RegionSupplier(
        name=row.name, siren=wrap(Siren, row.siren), tva_id=wrap(TvaId, row.tva_id)
    )


def regions_to_rows(
    product_id: str, regions: Mapping[str, RegionSupplier]
) -> list[ProductSupplierRegionRow]:
    return [
        ProductSupplierRegionRow(
            product_id=product_id,
            region=region,
            name=supplier.name,
            siren=raw(supplier.siren),
            tva_id=raw(supplier.tva_id),
        )
        for region, supplier in regions.items()
    ]
