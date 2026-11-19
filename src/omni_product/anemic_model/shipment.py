from __future__ import annotations

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from omni_product.database import Base


class ProductShipment(Base):
    """L'expédition d'un produit : poids et volume. Une ligne par produit, liée par son id."""

    __tablename__ = "product_shipment"

    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), primary_key=True)
    kilos: Mapped[float | None] = mapped_column(Float)
    volume: Mapped[str | None] = mapped_column(String)

    def __init__(
        self, product_id: str, kilos: float | None = None, volume: str | None = None
    ) -> None:
        self.product_id = product_id
        self.kilos = kilos
        self.volume = volume
