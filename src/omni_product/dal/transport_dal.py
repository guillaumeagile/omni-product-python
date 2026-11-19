"""Contexte Transport : les dimensions d'expédition d'un produit, liées par `product_id`."""

from sqlalchemy import Float, ForeignKey, String, delete
from sqlalchemy.orm import Mapped, Session, mapped_column

from omni_product.dal.value_object_type import ValueObjectType
from omni_product.database import Base
from omni_product.domain.model.product import ProductId


class ProductTransport(Base):
    __tablename__ = "product_transports"

    product_id: Mapped[ProductId] = mapped_column(
        ValueObjectType(ProductId, String()), ForeignKey("products.id"), primary_key=True
    )
    kilos: Mapped[float | None] = mapped_column(Float)
    volume: Mapped[str | None] = mapped_column(String)


def find(session: Session, product_id: ProductId) -> ProductTransport | None:
    return session.get(ProductTransport, product_id)


def replace(
    session: Session, product_id: ProductId, kilos: float | None, volume: str | None
) -> None:
    row = session.get(ProductTransport, product_id)
    if row is None:
        session.add(ProductTransport(product_id=product_id, kilos=kilos, volume=volume))
    else:
        row.kilos = kilos
        row.volume = volume


def delete_for(session: Session, product_id: ProductId) -> None:
    session.execute(delete(ProductTransport).where(ProductTransport.product_id == product_id))
