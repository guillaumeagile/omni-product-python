from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from omni_product.anemic_model import (
    Price,
    Product,
    ProductDiscount,
    ProductPrice,
    ProductStock,
    ProductSupplierRegion,
    ProductSupply,
    ProductTransport,
    RegionSupplier,
    Warehouse,
)


@dataclass
class ProductSheet:
    """La fiche d'un produit : le Catalogue et les données des autres contextes, assemblés.

    Les contextes restent des classes séparées en base. La fiche ne sert qu'à lire et écrire
    l'ensemble d'un coup, comme l'API le fait.
    """

    product: Product
    price: Price | None = None
    discounts: list[str] = field(default_factory=list[str])
    kilos: float | None = None
    volume: str | None = None
    quantity: int | None = None
    stock: int | None = None
    warehouse: Warehouse | None = None
    supplier_id: str | None = None
    suppliers_regions: dict[str, RegionSupplier] = field(default_factory=dict[str, RegionSupplier])


def find_all(session: Session) -> list[ProductSheet]:
    products = session.scalars(select(Product).order_by(Product.id)).all()
    return [_load(session, product) for product in products]


def find_by_id(session: Session, product_id: str) -> ProductSheet | None:
    product = session.get(Product, product_id)
    return None if product is None else _load(session, product)


def find_by_slug(session: Session, slug: str) -> Product | None:
    return session.scalars(select(Product).where(Product.slug == slug)).first()


def exists_by_slug(session: Session, slug: str) -> bool:
    return find_by_slug(session, slug) is not None


def save(session: Session, sheet: ProductSheet) -> ProductSheet:
    product = session.merge(sheet.product)
    _replace_context_rows(session, product.id, sheet)
    session.commit()
    return _load(session, product)


def delete_by_id(session: Session, product_id: str) -> None:
    product = session.get(Product, product_id)
    if product is not None:
        _delete_context_rows(session, product_id)
        session.delete(product)
        session.commit()


def delete_by_slug(session: Session, slug: str) -> None:
    product = find_by_slug(session, slug)
    if product is not None:
        delete_by_id(session, product.id)


def delete_all(session: Session) -> None:
    for product in session.scalars(select(Product)).all():
        delete_by_id(session, product.id)


def _load(session: Session, product: Product) -> ProductSheet:
    product_id = product.id
    price = session.get(ProductPrice, product_id)
    transport = session.get(ProductTransport, product_id)
    stock = session.get(ProductStock, product_id)
    supply = session.get(ProductSupply, product_id)
    discounts = session.scalars(
        select(ProductDiscount)
        .where(ProductDiscount.product_id == product_id)
        .order_by(ProductDiscount.id)
    ).all()
    regions = session.scalars(
        select(ProductSupplierRegion).where(ProductSupplierRegion.product_id == product_id)
    ).all()
    return ProductSheet(
        product=product,
        price=Price(price.base, price.tax, price.tax_rate) if price is not None else None,
        discounts=[row.discount for row in discounts],
        kilos=transport.kilos if transport is not None else None,
        volume=transport.volume if transport is not None else None,
        quantity=stock.quantity if stock is not None else None,
        stock=stock.stock if stock is not None else None,
        warehouse=(
            Warehouse(stock.warehouse_location)
            if stock is not None and stock.warehouse_location is not None
            else None
        ),
        supplier_id=supply.supplier_id if supply is not None else None,
        suppliers_regions={row.region: row.supplier for row in regions},
    )


def _replace_context_rows(session: Session, product_id: str, sheet: ProductSheet) -> None:
    """Remplace les lignes des contextes : une sauvegarde écrase l'ancienne fiche, comme un PUT."""
    _delete_context_rows(session, product_id)
    if sheet.price is not None:
        session.merge(
            ProductPrice(
                product_id=product_id,
                base=sheet.price.base,
                tax=sheet.price.tax,
                tax_rate=sheet.price.tax_rate,
            )
        )
    session.add_all(ProductDiscount(product_id, discount) for discount in sheet.discounts)
    session.merge(ProductTransport(product_id=product_id, kilos=sheet.kilos, volume=sheet.volume))
    session.merge(
        ProductStock(
            product_id=product_id,
            quantity=sheet.quantity,
            stock=sheet.stock,
            warehouse_location=sheet.warehouse.location if sheet.warehouse else None,
        )
    )
    session.merge(ProductSupply(product_id=product_id, supplier_id=sheet.supplier_id))
    session.add_all(
        ProductSupplierRegion(product_id, region, supplier)
        for region, supplier in sheet.suppliers_regions.items()
    )


def _delete_context_rows(session: Session, product_id: str) -> None:
    for model in (
        ProductPrice,
        ProductDiscount,
        ProductTransport,
        ProductStock,
        ProductSupply,
        ProductSupplierRegion,
    ):
        session.execute(delete(model).where(model.product_id == product_id))
