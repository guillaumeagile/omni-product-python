from sqlalchemy import select
from sqlalchemy.orm import Session

from omni_product.anemic_model import Product


def find_all(session: Session) -> list[Product]:
    return list(session.scalars(select(Product).order_by(Product.id)))


def find_by_id(session: Session, product_id: str) -> Product | None:
    return session.get(Product, product_id)


def save(session: Session, product: Product) -> Product:
    saved = session.merge(product)
    session.commit()
    return saved


def delete_by_id(session: Session, product_id: str) -> None:
    product = find_by_id(session, product_id)
    if product is not None:
        session.delete(product)
        session.commit()


def delete_all(session: Session) -> None:
    for product in find_all(session):
        session.delete(product)
    session.commit()


def mark_for_deletion_by_supplier_id(session: Session, supplier_id: str) -> None:
    """Marque les produits du fournisseur à supprimer. Pas de commit : l'appelant valide."""
    for product in session.scalars(select(Product).where(Product.supplier_id == supplier_id)):
        session.delete(product)
