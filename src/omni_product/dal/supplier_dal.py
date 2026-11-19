from sqlalchemy import ColumnElement, select
from sqlalchemy.orm import Session

from omni_product.dal import product_dal
from omni_product.dal.mapping import product_sourcing, suppliers
from omni_product.domain.model.product_values import (
    Country,
    ProductId,
    Region,
    SupplierId,
    SupplierName,
)
from omni_product.domain.model.supplier import Supplier


def find_all(session: Session) -> list[Supplier]:
    return list(session.scalars(select(Supplier).order_by(suppliers.c.id)))


def find_by_id(session: Session, supplier_id: str) -> Supplier | None:
    return session.get(Supplier, SupplierId(supplier_id))


def find_by_country(session: Session, country: str) -> list[Supplier]:
    return _find_all_where(session, suppliers.c.country == Country(country))


def find_by_region(session: Session, region: str) -> list[Supplier]:
    return _find_all_where(session, suppliers.c.region == Region(region))


def find_by_name(session: Session, name: str) -> Supplier | None:
    return session.scalars(select(Supplier).where(suppliers.c.name == SupplierName(name))).first()


def find_by_product_id(session: Session, product_id: str) -> list[Supplier]:
    """Requête SQL : le lien produit → fournisseur passe par la table `product_sourcing`."""
    statement = (
        select(Supplier)
        .join(product_sourcing, product_sourcing.c.supplier_id == suppliers.c.id)
        .where(product_sourcing.c.product_id == ProductId(product_id))
        .order_by(suppliers.c.id)
    )
    return list(session.scalars(statement))


def save(session: Session, supplier: Supplier) -> Supplier:
    saved = session.merge(supplier)
    session.commit()
    return saved


def delete(session: Session, supplier: Supplier) -> None:
    # Un fournisseur supprimé emporte ses produits (comportement d'origine, cascade Java).
    product_ids = session.scalars(
        select(product_sourcing.c.product_id).where(product_sourcing.c.supplier_id == supplier.id)
    ).all()
    for product_id in product_ids:
        product_dal.delete_by_id(session, product_id.value)
    session.delete(supplier)
    session.commit()


def delete_all(session: Session) -> None:
    for supplier in find_all(session):
        delete(session, supplier)


def _find_all_where(session: Session, criterion: ColumnElement[bool]) -> list[Supplier]:
    statement = select(Supplier).where(criterion).order_by(suppliers.c.id)
    return list(session.scalars(statement))
