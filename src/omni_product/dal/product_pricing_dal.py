from sqlalchemy import select
from sqlalchemy.orm import Session

from omni_product.anemic_model import Product, ProductPricing


def find_by_product_id(session: Session, product_id: str) -> ProductPricing | None:
    return session.get(ProductPricing, product_id)


def save(session: Session, pricing: ProductPricing) -> ProductPricing:
    saved = session.merge(pricing)
    session.commit()
    return saved


def delete_by_product_id(session: Session, product_id: str) -> None:
    pricing = find_by_product_id(session, product_id)
    if pricing is not None:
        session.delete(pricing)
        session.commit()


def mark_for_deletion_by_supplier_id(session: Session, supplier_id: str) -> None:
    """Marque les tarifs des produits du fournisseur. Pas de commit : l'appelant valide."""
    statement = (
        select(ProductPricing)
        .join(Product, Product.id == ProductPricing.product_id)
        .where(Product.supplier_id == supplier_id)
    )
    for pricing in session.scalars(statement):
        session.delete(pricing)
