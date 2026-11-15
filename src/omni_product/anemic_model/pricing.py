from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from omni_product.database import Base


# Contexte Pricing : ce que coûte un produit, et les remises qui s'y appliquent.
@dataclass
class Price:
    base: float | None = None
    tax: float | None = None
    tax_rate: float | None = None


class ProductPrice(Base):
    __tablename__ = "product_prices"

    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), primary_key=True)
    base: Mapped[float | None] = mapped_column(Float)
    tax: Mapped[float | None] = mapped_column(Float)
    tax_rate: Mapped[float | None] = mapped_column(Float)


class ProductDiscount(Base):
    __tablename__ = "product_discounts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"))
    discount: Mapped[str] = mapped_column(String)

    def __init__(self, product_id: str, discount: str) -> None:
        self.product_id = product_id
        self.discount = discount
