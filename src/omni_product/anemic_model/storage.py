"""Storage : ce qu'on a en stock, et où."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, composite, mapped_column

from omni_product.database import Base


@dataclass
class Warehouse:
    location: str | None = None


class ProductStorage(Base):
    __tablename__ = "product_storage"

    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), primary_key=True)
    quantity: Mapped[int | None] = mapped_column(Integer)
    stock: Mapped[int | None] = mapped_column(Integer)
    warehouse: Mapped[Warehouse] = composite(Warehouse, mapped_column("warehouse_location", String))
