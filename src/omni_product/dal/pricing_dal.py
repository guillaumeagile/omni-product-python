"""Contexte Pricing : le prix et les remises d'un produit, liés par `product_id`."""

from sqlalchemy import Float, ForeignKey, String, delete, select
from sqlalchemy.orm import Mapped, Session, composite, mapped_column

from omni_product.anemic_model import Price
from omni_product.database import Base


class ProductPrice(Base):
    __tablename__ = "product_prices"

    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), primary_key=True)
    price: Mapped[Price] = composite(
        Price,
        mapped_column("base", Float),
        mapped_column("tax", Float),
        mapped_column("tax_rate", Float),
    )


class ProductDiscount(Base):
    __tablename__ = "product_discounts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"))
    discount: Mapped[str] = mapped_column(String)

    def __init__(self, product_id: str, discount: str) -> None:
        self.product_id = product_id
        self.discount = discount


def find_price(session: Session, product_id: str) -> Price | None:
    row = session.get(ProductPrice, product_id)
    return row.price if row is not None else None


def find_discounts(session: Session, product_id: str) -> list[str]:
    statement = (
        select(ProductDiscount.discount)
        .where(ProductDiscount.product_id == product_id)
        .order_by(ProductDiscount.id)
    )
    return list(session.scalars(statement))


def replace(session: Session, product_id: str, price: Price | None, discounts: list[str]) -> None:
    """Un prix absent laisse le prix en place ; les remises sont toujours remplacées."""
    if price is not None:
        row = session.get(ProductPrice, product_id)
        if row is None:
            session.add(ProductPrice(product_id=product_id, price=price))
        else:
            row.price = price
    session.execute(delete(ProductDiscount).where(ProductDiscount.product_id == product_id))
    session.add_all(
        ProductDiscount(product_id=product_id, discount=discount) for discount in discounts
    )


def delete_for(session: Session, product_id: str) -> None:
    session.execute(delete(ProductDiscount).where(ProductDiscount.product_id == product_id))
    session.execute(delete(ProductPrice).where(ProductPrice.product_id == product_id))
