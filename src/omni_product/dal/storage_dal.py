"""Contexte Storage : quantité, stock et entrepôt d'un produit, liés par `product_id`."""

from sqlalchemy import ForeignKey, Integer, String, delete
from sqlalchemy.orm import Mapped, Session, composite, mapped_column

from omni_product.anemic_model import Warehouse
from omni_product.database import Base


class ProductStock(Base):
    __tablename__ = "product_stocks"

    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), primary_key=True)
    quantity: Mapped[int | None] = mapped_column(Integer)
    stock: Mapped[int | None] = mapped_column(Integer)
    warehouse: Mapped[Warehouse] = composite(Warehouse, mapped_column("warehouse_location", String))


def find(session: Session, product_id: str) -> ProductStock | None:
    return session.get(ProductStock, product_id)


def replace(
    session: Session,
    product_id: str,
    quantity: int | None,
    stock: int | None,
    warehouse: Warehouse | None,
) -> None:
    """Un entrepôt absent laisse l'entrepôt en place ; quantité et stock sont toujours remplacés."""
    row = session.get(ProductStock, product_id)
    if row is None:
        session.add(
            ProductStock(product_id=product_id, quantity=quantity, stock=stock, warehouse=warehouse)
        )
        return
    row.quantity = quantity
    row.stock = stock
    if warehouse is not None:
        row.warehouse = warehouse


def delete_for(session: Session, product_id: str) -> None:
    session.execute(delete(ProductStock).where(ProductStock.product_id == product_id))
