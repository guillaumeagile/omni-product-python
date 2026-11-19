from sqlalchemy import select
from sqlalchemy.orm import Session

from omni_product.anemic_model import Product, ProductStock


def find_by_product_id(session: Session, product_id: str) -> ProductStock | None:
    return session.get(ProductStock, product_id)


def save(session: Session, stock: ProductStock) -> ProductStock:
    saved = session.merge(stock)
    session.commit()
    return saved


def delete_by_product_id(session: Session, product_id: str) -> None:
    stock = find_by_product_id(session, product_id)
    if stock is not None:
        session.delete(stock)
        session.commit()


def mark_for_deletion_by_supplier_id(session: Session, supplier_id: str) -> None:
    """Marque les stocks des produits du fournisseur. Pas de commit : l'appelant valide."""
    statement = (
        select(ProductStock)
        .join(Product, Product.id == ProductStock.product_id)
        .where(Product.supplier_id == supplier_id)
    )
    for stock in session.scalars(statement):
        session.delete(stock)
