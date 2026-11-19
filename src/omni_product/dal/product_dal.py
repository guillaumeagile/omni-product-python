"""Contexte Catalog : le produit et ses images. Les autres contextes ont leurs modules à côté."""

from sqlalchemy import ForeignKey, String, delete, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from omni_product.anemic_model import Product
from omni_product.dal import pricing_dal, storage_dal, supplier_dal, transport_dal
from omni_product.database import Base


class ProductImage(Base):
    __tablename__ = "product_images"

    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), primary_key=True)
    image_key: Mapped[str] = mapped_column(String, primary_key=True)
    image_detail: Mapped[str | None] = mapped_column(String)

    def __init__(self, product_id: str, image_key: str, image_detail: str | None) -> None:
        self.product_id = product_id
        self.image_key = image_key
        self.image_detail = image_detail


def find_all(session: Session) -> list[Product]:
    return list(session.scalars(select(Product).order_by(Product.id)))


def find_by_id(session: Session, product_id: str) -> Product | None:
    return session.get(Product, product_id)


def find_by_slug(session: Session, slug: str) -> Product | None:
    return session.scalars(select(Product).where(Product.slug == slug)).first()


def find_by_supplier_id(session: Session, supplier_id: str) -> list[Product]:
    return list(
        session.scalars(
            select(Product).where(Product.supplier_id == supplier_id).order_by(Product.id)
        )
    )


def exists_by_slug(session: Session, slug: str) -> bool:
    return find_by_slug(session, slug) is not None


def find_images(session: Session, product_id: str) -> dict[str, str | None]:
    statement = select(ProductImage).where(ProductImage.product_id == product_id)
    return {row.image_key: row.image_detail for row in session.scalars(statement)}


def merge(session: Session, product: Product) -> Product:
    """Fusionne le produit sans valider : le service écrit les autres contextes puis valide."""
    return session.merge(product)


def replace_images(session: Session, product_id: str, images: dict[str, str | None]) -> None:
    session.execute(delete(ProductImage).where(ProductImage.product_id == product_id))
    session.add_all(
        ProductImage(product_id=product_id, image_key=key, image_detail=detail)
        for key, detail in images.items()
    )


def save(session: Session, product: Product) -> Product:
    saved = merge(session, product)
    session.commit()
    return saved


def delete_by_id(session: Session, product_id: str) -> None:
    product = find_by_id(session, product_id)
    if product is not None:
        _delete(session, product)
        session.commit()


def delete_by_slug(session: Session, slug: str) -> None:
    product = find_by_slug(session, slug)
    if product is not None:
        _delete(session, product)
        session.commit()


def delete_by_supplier_id(session: Session, supplier_id: str) -> None:
    for product in find_by_supplier_id(session, supplier_id):
        _delete(session, product)
    session.commit()


def delete_all(session: Session) -> None:
    for product in find_all(session):
        _delete(session, product)
    session.commit()


def _delete(session: Session, product: Product) -> None:
    """Supprime le produit et les lignes de chaque contexte qui le référencent."""
    session.execute(delete(ProductImage).where(ProductImage.product_id == product.id))
    pricing_dal.delete_for(session, product.id)
    transport_dal.delete_for(session, product.id)
    storage_dal.delete_for(session, product.id)
    supplier_dal.delete_regions_for(session, product.id)
    session.delete(product)
