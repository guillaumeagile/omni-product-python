from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, composite, mapped_column

from omni_product.database import Base


@dataclass
class Warehouse:
    location: str | None = None


class ProductStock(Base):
    """Le stock d'un produit, dans le contexte Storage. Lié au produit par `product_id`."""

    __tablename__ = "product_stocks"

    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), primary_key=True)
    quantity: Mapped[int | None] = mapped_column(Integer)
    stock: Mapped[int | None] = mapped_column(Integer)
    warehouse: Mapped[Warehouse] = composite(Warehouse, mapped_column("warehouse_location", String))
