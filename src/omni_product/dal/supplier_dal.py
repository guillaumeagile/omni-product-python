from sqlalchemy import select
from sqlalchemy.orm import Session

from omni_product.dal.conversion import supplier_from_row, supplier_to_row
from omni_product.dal.rows import ProductRow, SupplierRow
from omni_product.domain.model.supplier import Supplier


def find_all(session: Session) -> list[Supplier]:
    return [
        supplier_from_row(row)
        for row in session.scalars(select(SupplierRow).order_by(SupplierRow.id))
    ]


def find_by_id(session: Session, supplier_id: str) -> Supplier | None:
    row = session.get(SupplierRow, supplier_id)
    return None if row is None else supplier_from_row(row)


def find_by_country(session: Session, country: str) -> list[Supplier]:
    return _find_all_where(session, SupplierRow.country == country)


def find_by_region(session: Session, region: str) -> list[Supplier]:
    return _find_all_where(session, SupplierRow.region == region)


def find_by_name(session: Session, name: str) -> Supplier | None:
    row = session.scalars(select(SupplierRow).where(SupplierRow.name == name)).first()
    return None if row is None else supplier_from_row(row)


def find_by_product_id(session: Session, product_id: str) -> list[Supplier]:
    """Requête SQL à la place du filtrage en mémoire qui causait le lazy loading Java."""
    statement = (
        select(SupplierRow)
        .join(ProductRow, ProductRow.supplier_id == SupplierRow.id)
        .where(ProductRow.id == product_id)
        .order_by(SupplierRow.id)
    )
    return [supplier_from_row(row) for row in session.scalars(statement)]


def save(session: Session, supplier: Supplier) -> Supplier:
    session.merge(supplier_to_row(supplier))
    session.commit()
    return supplier


def delete(session: Session, supplier: Supplier) -> None:
    row = session.get(SupplierRow, supplier.id)
    if row is not None:
        session.delete(row)
        session.commit()


def delete_all(session: Session) -> None:
    for row in list(session.scalars(select(SupplierRow))):
        session.delete(row)
    session.commit()


def _find_all_where(session: Session, criterion: object) -> list[Supplier]:
    statement = select(SupplierRow).where(criterion).order_by(SupplierRow.id)  # pyright: ignore[reportArgumentType]
    return [supplier_from_row(row) for row in session.scalars(statement)]
