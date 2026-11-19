from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, composite, mapped_column

from omni_product.database import Base


@dataclass
class Warehouse:
    location: str | None = None


class ProductStock(Base):
    """Le stock d'un produit : une ligne par produit, reliée par son identifiant."""

    __tablename__ = "product_stock"

    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), primary_key=True)
    quantity: Mapped[int | None] = mapped_column(Integer)
    stock: Mapped[int | None] = mapped_column(Integer)
    warehouse: Mapped[Warehouse | None] = composite(
        Warehouse, mapped_column("warehouse_location", String)
    )

    def __init__(
        self,
        product_id: str,
        quantity: int | None = None,
        stock: int | None = None,
        warehouse: Warehouse | None = None,
    ) -> None:
        self.product_id = product_id
        self.quantity = quantity
        self.stock = stock
        self.warehouse = warehouse
