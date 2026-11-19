from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from omni_product.dal.conversion import product_from_row, product_to_row
from omni_product.dal.rows import (
    ProductDiscountRow,
    ProductPriceRow,
    ProductRow,
    ProductShipmentRow,
    ProductStockRow,
    ProductSupplierRegionRow,
)
from omni_product.domain.model.product import Product

# Lignes liées à un produit, à supprimer avant le produit lui-même.
_DETAIL_ROWS = (
    ProductStockRow,
    ProductShipmentRow,
    ProductPriceRow,
    ProductDiscountRow,
    ProductSupplierRegionRow,
)


def find_all(session: Session) -> list[Product]:
    return [
        product_from_row(row) for row in session.scalars(select(ProductRow).order_by(ProductRow.id))
    ]


def find_by_id(session: Session, product_id: str) -> Product | None:
    row = session.get(ProductRow, product_id)
    return None if row is None else product_from_row(row)


def find_by_slug(session: Session, slug: str) -> Product | None:
    row = _find_row_by_slug(session, slug)
    return None if row is None else product_from_row(row)


def exists_by_slug(session: Session, slug: str) -> bool:
    return _find_row_by_slug(session, slug) is not None


def save(session: Session, product: Product) -> Product:
    session.merge(product_to_row(product))
    session.commit()
    return product


def delete_by_id(session: Session, product_id: str) -> None:
    row = session.get(ProductRow, product_id)
    if row is not None:
        _delete_row(session, row)


def delete_by_slug(session: Session, slug: str) -> None:
    row = _find_row_by_slug(session, slug)
    if row is not None:
        _delete_row(session, row)


def delete_by_supplier_id(session: Session, supplier_id: str) -> None:
    for row in list(
        session.scalars(select(ProductRow).where(ProductRow.supplier_id == supplier_id))
    ):
        _delete_details(session, row.id)
        session.delete(row)
    session.commit()


def delete_all(session: Session) -> None:
    for table in _DETAIL_ROWS:
        session.execute(delete(table))
    for row in list(session.scalars(select(ProductRow))):
        session.delete(row)
    session.commit()


def _find_row_by_slug(session: Session, slug: str) -> ProductRow | None:
    return session.scalars(select(ProductRow).where(ProductRow.slug == slug)).first()


def _delete_row(session: Session, row: ProductRow) -> None:
    _delete_details(session, row.id)
    session.delete(row)
    session.commit()


def _delete_details(session: Session, product_id: str) -> None:
    """Supprime les lignes liées au produit (stock, expédition, prix…) avant le produit lui-même."""
    for table in _DETAIL_ROWS:
        session.execute(delete(table).where(table.product_id == product_id))
