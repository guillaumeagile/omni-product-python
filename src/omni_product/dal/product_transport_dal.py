from sqlalchemy import select
from sqlalchemy.orm import Session

from omni_product.anemic_model import Product, ProductTransport


def find_by_product_id(session: Session, product_id: str) -> ProductTransport | None:
    return session.get(ProductTransport, product_id)


def save(session: Session, transport: ProductTransport) -> ProductTransport:
    saved = session.merge(transport)
    session.commit()
    return saved


def delete_by_product_id(session: Session, product_id: str) -> None:
    transport = find_by_product_id(session, product_id)
    if transport is not None:
        session.delete(transport)
        session.commit()


def mark_for_deletion_by_supplier_id(session: Session, supplier_id: str) -> None:
    """Marque les transports des produits du fournisseur. Pas de commit : l'appelant valide."""
    statement = (
        select(ProductTransport)
        .join(Product, Product.id == ProductTransport.product_id)
        .where(Product.supplier_id == supplier_id)
    )
    for transport in session.scalars(statement):
        session.delete(transport)
