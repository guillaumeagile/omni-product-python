"""Contexte Catalog : le produit et ses images. Les autres contextes ont leurs modules à côté."""

from datetime import date

from sqlalchemy import ForeignKey, String, delete, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from omni_product.dal import pricing_dal, storage_dal, supplier_dal, transport_dal
from omni_product.dal.model_mapping import ProductRecord, products
from omni_product.dal.value_object_type import ValueObjectType
from omni_product.database import Base
from omni_product.domain.model.product import (
    NonExpiring,
    Perishable,
    Product,
    ProductId,
    ShelfLife,
    ShelfLifeDays,
    Slug,
)
from omni_product.domain.model.supplier import SupplierId


class ProductImage(Base):
    __tablename__ = "product_images"

    product_id: Mapped[ProductId] = mapped_column(
        ValueObjectType(ProductId, String()), ForeignKey("products.id"), primary_key=True
    )
    image_key: Mapped[str] = mapped_column(String, primary_key=True)
    image_detail: Mapped[str | None] = mapped_column(String)

    def __init__(self, product_id: ProductId, image_key: str, image_detail: str | None) -> None:
        self.product_id = product_id
        self.image_key = image_key
        self.image_detail = image_detail


def find_all(session: Session) -> list[Product]:
    return [_to_product(record) for record in _records(session)]


def find_by_id(session: Session, product_id: ProductId) -> Product | None:
    record = session.get(ProductRecord, product_id)
    return _to_product(record) if record is not None else None


def find_by_slug(session: Session, slug: Slug) -> Product | None:
    record = _record_by_slug(session, slug)
    return _to_product(record) if record is not None else None


def find_by_supplier_id(session: Session, supplier_id: SupplierId) -> list[Product]:
    return [_to_product(record) for record in _records_of_supplier(session, supplier_id)]


def exists_by_slug(session: Session, slug: Slug) -> bool:
    return _record_by_slug(session, slug) is not None


def find_images(session: Session, product_id: ProductId) -> dict[str, str | None]:
    statement = select(ProductImage).where(ProductImage.product_id == product_id)
    return {row.image_key: row.image_detail for row in session.scalars(statement)}


def merge(session: Session, product: Product) -> Product:
    """Fusionne le produit sans valider : le service écrit les autres contextes puis valide."""
    return _to_product(session.merge(_to_record(product)))


def replace_images(session: Session, product_id: ProductId, images: dict[str, str | None]) -> None:
    session.execute(delete(ProductImage).where(ProductImage.product_id == product_id))
    session.add_all(
        ProductImage(product_id=product_id, image_key=key, image_detail=detail)
        for key, detail in images.items()
    )


def save(session: Session, product: Product) -> Product:
    saved = merge(session, product)
    session.commit()
    return saved


def delete_by_id(session: Session, product_id: ProductId) -> None:
    record = session.get(ProductRecord, product_id)
    if record is not None:
        _delete(session, record)
        session.commit()


def delete_by_slug(session: Session, slug: Slug) -> None:
    record = _record_by_slug(session, slug)
    if record is not None:
        _delete(session, record)
        session.commit()


def delete_by_supplier_id(session: Session, supplier_id: SupplierId) -> None:
    for record in _records_of_supplier(session, supplier_id):
        _delete(session, record)
    session.commit()


def delete_all(session: Session) -> None:
    for record in _records(session):
        _delete(session, record)
    session.commit()


def _records(session: Session) -> list[ProductRecord]:
    return list(session.scalars(select(ProductRecord).order_by(products.c.id)))


def _records_of_supplier(session: Session, supplier_id: SupplierId) -> list[ProductRecord]:
    statement = (
        select(ProductRecord).where(products.c.supplier_id == supplier_id).order_by(products.c.id)
    )
    return list(session.scalars(statement))


def _record_by_slug(session: Session, slug: Slug) -> ProductRecord | None:
    return session.scalars(select(ProductRecord).where(products.c.slug == slug)).first()


def _delete(session: Session, record: ProductRecord) -> None:
    """Supprime le produit et les lignes de chaque contexte qui le référencent."""
    session.execute(delete(ProductImage).where(ProductImage.product_id == record.id))
    pricing_dal.delete_for(session, record.id)
    transport_dal.delete_for(session, record.id)
    storage_dal.delete_for(session, record.id)
    supplier_dal.delete_regions_for(session, record.id)
    session.delete(record)


def _to_record(product: Product) -> ProductRecord:
    """La variante s'aplatit : `kind` la nomme, les colonnes périssables restent nulles sinon."""
    expiration_date, shelf_life_days = _perishable_columns(product.shelf_life)
    return ProductRecord(
        id=product.id,
        kind=_kind_of(product.shelf_life),
        name=product.name,
        slug=product.slug,
        supplier_id=product.supplier_id,
        expiration_date=expiration_date,
        shelf_life_days=shelf_life_days,
    )


def _to_product(record: ProductRecord) -> Product:
    return Product(
        id=record.id,
        name=record.name,
        slug=record.slug,
        supplier_id=record.supplier_id,
        shelf_life=_shelf_life_of(record),
    )


def _kind_of(shelf_life: ShelfLife | None) -> str:
    match shelf_life:
        case Perishable():
            return "perishable"
        case NonExpiring():
            return "non_expiring"
        case None:
            return "standard"


def _perishable_columns(shelf_life: ShelfLife | None) -> tuple[date | None, ShelfLifeDays | None]:
    match shelf_life:
        case Perishable(expiration_date=expiration_date, shelf_life_days=shelf_life_days):
            return expiration_date, shelf_life_days
        case NonExpiring() | None:
            return None, None


def _shelf_life_of(record: ProductRecord) -> ShelfLife | None:
    match record.kind:
        case "perishable":
            return Perishable(record.expiration_date, record.shelf_life_days)
        case "non_expiring":
            return NonExpiring()
        case _:
            return None
