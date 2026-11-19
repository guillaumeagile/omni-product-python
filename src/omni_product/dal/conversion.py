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
from omni_product.domain.model.pricing import Price, ProductPrice
from omni_product.domain.model.product import NonExpiringProduct, PerishableProduct, Product
from omni_product.domain.model.shipment import ProductShipment
from omni_product.domain.model.stock import ProductStock, Warehouse
from omni_product.domain.model.supplier import Supplier
from omni_product.domain.model.supplier_region import RegionSupplier


def product_from_row(row: ProductRow) -> Product:
    images: dict[str, str | None] = {
        key: image.image_detail for key, image in row.image_rows.items()
    }
    match row.kind:
        case "perishable":
            return PerishableProduct(
                id=row.id,
                name=row.name,
                slug=row.slug,
                supplier_id=row.supplier_id,
                images=images,
                expiration_date=row.expiration_date,
                shelf_life_days=row.shelf_life_days,
            )
        case "non_expiring":
            return NonExpiringProduct(
                id=row.id, name=row.name, slug=row.slug, supplier_id=row.supplier_id, images=images
            )
        case _:
            return Product(
                id=row.id, name=row.name, slug=row.slug, supplier_id=row.supplier_id, images=images
            )


def product_to_row(product: Product) -> ProductRow:
    perishable = product if isinstance(product, PerishableProduct) else None
    return ProductRow(
        id=product.id,
        kind=_kind_of(product),
        name=product.name,
        slug=product.slug,
        supplier_id=product.supplier_id,
        expiration_date=perishable.expiration_date if perishable else None,
        shelf_life_days=perishable.shelf_life_days if perishable else None,
        image_rows={
            key: ProductImageRow(product_id=product.id, image_key=key, image_detail=detail)
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
    price = None if all(value is None for value in values) else Price(*values)
    return ProductPrice(product_id=row.product_id, price=price)


def price_to_row(price: ProductPrice) -> ProductPriceRow:
    value = price.price
    return ProductPriceRow(
        product_id=price.product_id,
        price_base=value.base if value else None,
        price_tax=value.tax if value else None,
        price_tax_rate=value.tax_rate if value else None,
    )


def shipment_from_row(row: ProductShipmentRow) -> ProductShipment:
    return ProductShipment(product_id=row.product_id, kilos=row.kilos, volume=row.volume)


def shipment_to_row(shipment: ProductShipment) -> ProductShipmentRow:
    return ProductShipmentRow(
        product_id=shipment.product_id, kilos=shipment.kilos, volume=shipment.volume
    )


def stock_from_row(row: ProductStockRow) -> ProductStock:
    warehouse = None if row.warehouse_location is None else Warehouse(row.warehouse_location)
    return ProductStock(
        product_id=row.product_id, quantity=row.quantity, stock=row.stock, warehouse=warehouse
    )


def stock_to_row(stock: ProductStock) -> ProductStockRow:
    return ProductStockRow(
        product_id=stock.product_id,
        quantity=stock.quantity,
        stock=stock.stock,
        warehouse_location=stock.warehouse.location if stock.warehouse else None,
    )


def supplier_from_row(row: SupplierRow) -> Supplier:
    return Supplier(
        id=row.id,
        name=row.name,
        contact_email=row.contact_email,
        contact_phone=row.contact_phone,
        country=row.country,
        region=row.region,
    )


def supplier_to_row(supplier: Supplier) -> SupplierRow:
    return SupplierRow(
        id=supplier.id,
        name=supplier.name,
        contact_email=supplier.contact_email,
        contact_phone=supplier.contact_phone,
        country=supplier.country,
        region=supplier.region,
    )


def region_from_row(row: ProductSupplierRegionRow) -> RegionSupplier:
    return RegionSupplier(name=row.name, siren=row.siren, tva_id=row.tva_id)


def regions_to_rows(
    product_id: str, regions: Mapping[str, RegionSupplier]
) -> list[ProductSupplierRegionRow]:
    return [
        ProductSupplierRegionRow(
            product_id=product_id,
            region=region,
            name=supplier.name,
            siren=supplier.siren,
            tva_id=supplier.tva_id,
        )
        for region, supplier in regions.items()
    ]
