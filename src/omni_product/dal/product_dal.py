from sqlalchemy import select
from sqlalchemy.orm import Session

from omni_product.anemic_model import Product


def find_all(session: Session) -> list[Product]:
    return list(session.scalars(select(Product).order_by(Product.id)))


def find_by_id(session: Session, product_id: str) -> Product | None:
    return session.get(Product, product_id)


def find_by_slug(session: Session, slug: str) -> Product | None:
    return session.scalars(select(Product).where(Product.slug == slug)).first()


def exists_by_slug(session: Session, slug: str) -> bool:
    return find_by_slug(session, slug) is not None


def save(session: Session, product: Product) -> Product:
    """Fusionne le produit sans valider : le service valide la transaction complète."""
    return session.merge(product)


def delete(session: Session, product: Product) -> None:
    session.delete(product)
