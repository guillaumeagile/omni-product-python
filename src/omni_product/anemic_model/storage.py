from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from omni_product.database import Base


# Contexte Stockage : combien d'unités existent, et où elles sont rangées.
@dataclass
class Warehouse:
    location: str | None = None


class ProductStock(Base):
    __tablename__ = "product_stocks"

    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), primary_key=True)
    quantity: Mapped[int | None] = mapped_column(Integer)
    stock: Mapped[int | None] = mapped_column(Integer)
    warehouse_location: Mapped[str | None] = mapped_column(String)
