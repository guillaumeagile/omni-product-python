from __future__ import annotations

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from omni_product.database import Base


class ProductShipment(Base):
    """Les dimensions d'expédition d'un produit, dans le contexte Transport."""

    __tablename__ = "product_shipments"

    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), primary_key=True)
    kilos: Mapped[float | None] = mapped_column(Float)
    volume: Mapped[str | None] = mapped_column(String)
