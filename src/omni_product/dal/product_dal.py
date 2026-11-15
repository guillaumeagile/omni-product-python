from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from omni_product.anemic_model import (
    NonExpiringProduct,
    PerishableProduct,
    Price,
    Product,
    ProductId,
    ProductImage,
    ProductPrice,
    ProductStock,
    ProductSupply,
    ProductTransport,
    RegionSupplier,
    Slug,
    SupplierByRegion,
    Warehouse,
)
from omni_product.dal.rows import (
    ProductDiscountRow,
    ProductImageRow,
    ProductPriceRow,
    ProductRow,
    ProductStockRow,
    ProductSupplierRegionRow,
    ProductSupplyRow,
    ProductTransportRow,
)


@dataclass
class ProductSheet:
    """La fiche d'un produit : le Catalogue et les données des autres contextes, assemblés.

    Chaque contexte reste un objet du modèle, identifié par le produit. La fiche ne sert qu'à lire
    et écrire l'ensemble d'un coup, comme l'API le fait.
    """

    product: Product
    pricing: ProductPrice | None = None
    transport: ProductTransport | None = None
    stock: ProductStock | None = None
    supply: ProductSupply | None = None


def find_all(session: Session) -> list[ProductSheet]:
    rows = session.scalars(select(ProductRow).order_by(ProductRow.id)).all()
    return [_load(session, row) for row in rows]


def find_by_id(session: Session, product_id: ProductId) -> ProductSheet | None:
    row = session.get(ProductRow, product_id)
    return None if row is None else _load(session, row)


def find_by_slug(session: Session, slug: Slug) -> Product | None:
    row = session.scalars(select(ProductRow).where(ProductRow.slug == slug)).first()
    return None if row is None else _product(row)


def exists_by_slug(session: Session, slug: Slug) -> bool:
    return find_by_slug(session, slug) is not None


def save(session: Session, sheet: ProductSheet) -> ProductSheet:
    row = session.merge(_product_row(sheet.product))
    _replace_context_rows(session, sheet)
    session.commit()
    return _load(session, row)


def delete_by_id(session: Session, product_id: ProductId) -> None:
    row = session.get(ProductRow, product_id)
    if row is not None:
        _delete_context_rows(session, product_id)
        session.delete(row)
        session.commit()


def delete_by_slug(session: Session, slug: Slug) -> None:
    row = session.scalars(select(ProductRow).where(ProductRow.slug == slug)).first()
    if row is not None:
        delete_by_id(session, row.id)


def delete_all(session: Session) -> None:
    for row in session.scalars(select(ProductRow)).all():
        delete_by_id(session, row.id)


def _product(row: ProductRow) -> Product:
    images = tuple(
        ProductImage(key=image.image_key, detail=image.image_detail) for image in row.image_rows
    )
    match row.kind:
        case "perishable":
            return PerishableProduct(
                id=row.id,
                name=row.name,
                slug=row.slug,
                images=images,
                expiration_date=row.expiration_date,
                shelf_life_days=row.shelf_life_days,
            )
        case "non_expiring":
            return NonExpiringProduct(id=row.id, name=row.name, slug=row.slug, images=images)
        case _:
            return Product(id=row.id, name=row.name, slug=row.slug, images=images)


def _product_row(product: Product) -> ProductRow:
    perishable = product if isinstance(product, PerishableProduct) else None
    return ProductRow(
        id=product.id,
        kind=_kind_of(product),
        name=product.name,
        slug=product.slug,
        expiration_date=perishable.expiration_date if perishable else None,
        shelf_life_days=perishable.shelf_life_days if perishable else None,
        image_rows=[
            ProductImageRow(product_id=product.id, image_key=image.key, image_detail=image.detail)
            for image in product.images
        ],
    )


def _kind_of(product: Product) -> str:
    if isinstance(product, PerishableProduct):
        return "perishable"
    if isinstance(product, NonExpiringProduct):
        return "non_expiring"
    return "standard"


def _load(session: Session, row: ProductRow) -> ProductSheet:
    product_id = row.id
    price = session.get(ProductPriceRow, product_id)
    discounts = session.scalars(
        select(ProductDiscountRow)
        .where(ProductDiscountRow.product_id == product_id)
        .order_by(ProductDiscountRow.id)
    ).all()
    transport = session.get(ProductTransportRow, product_id)
    stock = session.get(ProductStockRow, product_id)
    supply = session.get(ProductSupplyRow, product_id)
    regions = session.scalars(
        select(ProductSupplierRegionRow).where(ProductSupplierRegionRow.product_id == product_id)
    ).all()
    return ProductSheet(
        product=_product(row),
        pricing=ProductPrice(
            id=product_id,
            price=(Price(price.base, price.tax, price.tax_rate) if price is not None else None),
            discounts=tuple(line.discount for line in discounts),
        ),
        transport=ProductTransport(
            id=product_id,
            kilos=transport.kilos if transport is not None else None,
            volume=transport.volume if transport is not None else None,
        ),
        stock=ProductStock(
            id=product_id,
            quantity=stock.quantity if stock is not None else None,
            stock=stock.stock if stock is not None else None,
            warehouse=(
                Warehouse(stock.warehouse_location)
                if stock is not None and stock.warehouse_location is not None
                else None
            ),
        ),
        supply=ProductSupply(
            id=product_id,
            supplier_id=supply.supplier_id if supply is not None else None,
            regions=tuple(
                SupplierByRegion(
                    region=line.region,
                    supplier=RegionSupplier(name=line.name, siren=line.siren, tva_id=line.tva_id),
                )
                for line in regions
            ),
        ),
    )


def _replace_context_rows(session: Session, sheet: ProductSheet) -> None:
    """Remplace les lignes des contextes : une sauvegarde écrase l'ancienne fiche, comme un PUT."""
    product_id = sheet.product.id
    _delete_context_rows(session, product_id)
    if sheet.pricing is not None:
        if sheet.pricing.price is not None:
            session.merge(
                ProductPriceRow(
                    product_id=product_id,
                    base=sheet.pricing.price.base,
                    tax=sheet.pricing.price.tax,
                    tax_rate=sheet.pricing.price.tax_rate,
                )
            )
        session.add_all(
            ProductDiscountRow(product_id=product_id, discount=discount)
            for discount in sheet.pricing.discounts
        )
    if sheet.transport is not None:
        session.merge(
            ProductTransportRow(
                product_id=product_id, kilos=sheet.transport.kilos, volume=sheet.transport.volume
            )
        )
    if sheet.stock is not None:
        session.merge(
            ProductStockRow(
                product_id=product_id,
                quantity=sheet.stock.quantity,
                stock=sheet.stock.stock,
                warehouse_location=(
                    sheet.stock.warehouse.location if sheet.stock.warehouse else None
                ),
            )
        )
    if sheet.supply is not None:
        session.merge(ProductSupplyRow(product_id=product_id, supplier_id=sheet.supply.supplier_id))
        session.add_all(
            ProductSupplierRegionRow(
                product_id=product_id,
                region=line.region,
                name=line.supplier.name,
                siren=line.supplier.siren,
                tva_id=line.supplier.tva_id,
            )
            for line in sheet.supply.regions
        )


def _delete_context_rows(session: Session, product_id: ProductId) -> None:
    for model in (
        ProductPriceRow,
        ProductDiscountRow,
        ProductTransportRow,
        ProductStockRow,
        ProductSupplyRow,
        ProductSupplierRegionRow,
    ):
        session.execute(delete(model).where(model.product_id == product_id))
