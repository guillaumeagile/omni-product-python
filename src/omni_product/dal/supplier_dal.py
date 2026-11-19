from sqlalchemy import ColumnElement, select
from sqlalchemy.orm import Session

from omni_product.dal import product_dal
from omni_product.dal.mapping import product_supply, suppliers
from omni_product.domain.model import Country, ProductId, Region, Supplier, SupplierId


def find_all(session: Session) -> list[Supplier]:
    return list(session.scalars(select(Supplier).order_by(suppliers.c.id)))


def find_by_id(session: Session, supplier_id: SupplierId) -> Supplier | None:
    return session.get(Supplier, supplier_id)


def find_by_country(session: Session, country: Country) -> list[Supplier]:
    return _find_all_where(session, suppliers.c.country == country)


def find_by_region(session: Session, region: Region) -> list[Supplier]:
    return _find_all_where(session, suppliers.c.region == region)


def find_by_name(session: Session, name: str) -> Supplier | None:
    return session.scalars(select(Supplier).where(suppliers.c.name == name)).first()


def find_by_product_id(session: Session, product_id: ProductId) -> list[Supplier]:
    """Le lien passe par l'identifiant du fournisseur que porte `ProductSupply`."""
    supplier_id = (
        select(product_supply.c.supplier_id)
        .where(product_supply.c.product_id == product_id)
        .scalar_subquery()
    )
    return _find_all_where(session, suppliers.c.id == supplier_id)


def save(session: Session, supplier: Supplier) -> Supplier:
    saved = session.merge(supplier)
    session.commit()
    return saved


def delete(session: Session, supplier: Supplier) -> None:
    """Supprime le fournisseur et ses produits (liés par `supplier_id`) en une transaction."""
    for product in product_dal.find_by_supplier_id(session, supplier.id):
        product_dal.remove(session, product)
    session.delete(supplier)
    session.commit()


def delete_all(session: Session) -> None:
    for supplier in find_all(session):
        session.delete(supplier)
    session.commit()


def _find_all_where(session: Session, criterion: ColumnElement[bool]) -> list[Supplier]:
    statement = select(Supplier).where(criterion).order_by(suppliers.c.id)
    return list(session.scalars(statement))
