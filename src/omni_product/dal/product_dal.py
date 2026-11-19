from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from omni_product.dal.mapping import product_supply, products
from omni_product.domain.model import (
    Product,
    ProductId,
    ProductPricing,
    ProductStorage,
    ProductSupply,
    ProductTransport,
    Slug,
    SupplierId,
)

type ProductContext = ProductPricing | ProductStorage | ProductTransport | ProductSupply

_CONTEXTS: tuple[type[ProductContext], ...] = (
    ProductPricing,
    ProductStorage,
    ProductTransport,
    ProductSupply,
)


def find_all(session: Session) -> list[Product]:
    return list(session.scalars(select(Product).order_by(products.c.id)))


def find_by_id(session: Session, product_id: ProductId) -> Product | None:
    return session.get(Product, product_id)


def find_by_slug(session: Session, slug: Slug) -> Product | None:
    return session.scalars(select(Product).where(products.c.slug == slug)).first()


def find_by_supplier_id(session: Session, supplier_id: SupplierId) -> list[Product]:
    statement = (
        select(Product)
        .join(product_supply, product_supply.c.product_id == products.c.id)
        .where(product_supply.c.supplier_id == supplier_id)
        .order_by(products.c.id)
    )
    return list(session.scalars(statement))


def exists_by_slug(session: Session, slug: Slug) -> bool:
    return find_by_slug(session, slug) is not None


def context_of[T: ProductContext](session: Session, context: type[T], product_id: ProductId) -> T:
    """Ce qu'un contexte sait du produit ; une instance vide s'il n'en sait encore rien."""
    return session.get(context, product_id) or context(id=product_id)


def save(session: Session, product: Product) -> Product:
    return save_with_contexts(session, product, [])


def save_with_contexts(
    session: Session, product: Product, contexts: Iterable[ProductContext]
) -> Product:
    """Enregistre le produit et ce que chaque contexte en sait, en une transaction."""
    saved = session.merge(product)
    for context in contexts:
        session.merge(context)
    session.commit()
    return saved


def delete_by_id(session: Session, product_id: ProductId) -> None:
    product = find_by_id(session, product_id)
    if product is not None:
        remove(session, product)
        session.commit()


def delete_by_slug(session: Session, slug: Slug) -> None:
    product = find_by_slug(session, slug)
    if product is not None:
        remove(session, product)
        session.commit()


def delete_all(session: Session) -> None:
    for product in find_all(session):
        remove(session, product)
    session.commit()


def remove(session: Session, product: Product) -> None:
    """Retire le produit de tous les contextes, sans valider : l'appelant termine la transaction."""
    for context in _CONTEXTS:
        known = session.get(context, product.id)
        if known is not None:
            session.delete(known)
    session.delete(product)
