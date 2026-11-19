from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, composite, mapped_column

from omni_product.database import Base


# Équivalent du @Embeddable Java : un composite SQLAlchemy mis à plat dans la table parente.
@dataclass
class Price:
    base: float | None = None
    tax: float | None = None
    tax_rate: float | None = None


class ProductPrice(Base):
    """Le prix d'un produit : une ligne par produit, liée par son identifiant."""

    __tablename__ = "product_price"

    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), primary_key=True)
    price: Mapped[Price | None] = composite(
        Price,
        mapped_column("price_base", Float),
        mapped_column("price_tax", Float),
        mapped_column("price_tax_rate", Float),
    )

    def __init__(self, product_id: str, price: Price | None = None) -> None:
        self.product_id = product_id
        self.price = price


# Équivalent de @ElementCollection : une ligne par remise, liée par l'identifiant du produit.
class ProductDiscount(Base):
    __tablename__ = "product_discounts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"))
    discount: Mapped[str] = mapped_column(String)

    def __init__(self, product_id: str, discount: str) -> None:
        self.product_id = product_id
        self.discount = discount
