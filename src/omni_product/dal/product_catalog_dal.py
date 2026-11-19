from sqlalchemy import select
from sqlalchemy.orm import Session

from omni_product.anemic_model import Product, ProductCatalog


def find_by_product_id(session: Session, product_id: str) -> ProductCatalog | None:
    return session.get(ProductCatalog, product_id)


def find_by_slug(session: Session, slug: str) -> ProductCatalog | None:
    return session.scalars(select(ProductCatalog).where(ProductCatalog.slug == slug)).first()


def save(session: Session, catalog: ProductCatalog) -> ProductCatalog:
    saved = session.merge(catalog)
    session.commit()
    return saved


def delete_by_product_id(session: Session, product_id: str) -> None:
    catalog = find_by_product_id(session, product_id)
    if catalog is not None:
        session.delete(catalog)
        session.commit()


def mark_for_deletion_by_supplier_id(session: Session, supplier_id: str) -> None:
    """Marque les fiches catalogue des produits du fournisseur. Pas de commit."""
    statement = (
        select(ProductCatalog)
        .join(Product, Product.id == ProductCatalog.product_id)
        .where(Product.supplier_id == supplier_id)
    )
    for catalog in session.scalars(statement):
        session.delete(catalog)
