from sqlalchemy import select
from sqlalchemy.orm import Session

from omni_product.anemic_model import ProductSupply, Supplier
from omni_product.dal import product_dal


def find_all(session: Session) -> list[Supplier]:
    return list(session.scalars(select(Supplier).order_by(Supplier.id)))


def find_by_id(session: Session, supplier_id: str) -> Supplier | None:
    return session.get(Supplier, supplier_id)


def find_by_country(session: Session, country: str) -> list[Supplier]:
    return _find_all_where(session, Supplier.country == country)


def find_by_region(session: Session, region: str) -> list[Supplier]:
    return _find_all_where(session, Supplier.region == region)


def find_by_name(session: Session, name: str) -> Supplier | None:
    return session.scalars(select(Supplier).where(Supplier.name == name)).first()


def find_by_product_id(session: Session, product_id: str) -> list[Supplier]:
    """Requête SQL à la place du filtrage en mémoire qui causait le lazy loading Java."""
    supplier_ids = select(ProductSupply.supplier_id).where(ProductSupply.product_id == product_id)
    return _find_all_where(session, Supplier.id.in_(supplier_ids))


def save(session: Session, supplier: Supplier) -> Supplier:
    saved = session.merge(supplier)
    session.commit()
    return saved


def delete(session: Session, supplier: Supplier) -> None:
    # Comportement conservé : supprimer un fournisseur supprime les produits qu'il fournit.
    product_ids = session.scalars(
        select(ProductSupply.product_id).where(ProductSupply.supplier_id == supplier.id)
    ).all()
    for product_id in product_ids:
        product_dal.delete_by_id(session, product_id)
    session.delete(supplier)
    session.commit()


def delete_all(session: Session) -> None:
    for supplier in find_all(session):
        session.delete(supplier)
    session.commit()


def _find_all_where(session: Session, criterion: object) -> list[Supplier]:
    statement = select(Supplier).where(criterion).order_by(Supplier.id)  # pyright: ignore[reportArgumentType]
    return list(session.scalars(statement))
