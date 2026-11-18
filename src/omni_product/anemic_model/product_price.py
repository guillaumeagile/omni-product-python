from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.orm import Mapped, composite, mapped_column, relationship

from omni_product.database import Base

_ROW_CASCADE = "all, delete-orphan"


# Équivalent d'un @Embeddable Java : un composite SQLAlchemy mis à plat dans la table parente.
@dataclass
class Price:
    base: float | None = None
    tax: float | None = None
    tax_rate: float | None = None


class ProductDiscount(Base):
    __tablename__ = "product_discounts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("product_prices.product_id"))
    discount: Mapped[str] = mapped_column(String)

    def __init__(self, discount: str) -> None:
        self.discount = discount


class ProductPrice(Base):
    """Le prix d'un produit, dans le contexte Pricing. Lié au produit par `product_id`."""

    __tablename__ = "product_prices"

    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), primary_key=True)
    price: Mapped[Price] = composite(
        Price,
        mapped_column("price_base", Float),
        mapped_column("price_tax", Float),
        mapped_column("price_tax_rate", Float),
    )
    discount_rows: Mapped[list[ProductDiscount]] = relationship(
        cascade=_ROW_CASCADE, order_by=ProductDiscount.id
    )
    discounts: AssociationProxy[list[str]] = association_proxy(
        "discount_rows", "discount", creator=ProductDiscount
    )
