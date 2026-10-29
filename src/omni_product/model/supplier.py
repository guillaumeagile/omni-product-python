from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from omni_product.database import Base

if TYPE_CHECKING:
    from omni_product.model.product import Product


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str | None] = mapped_column(String)
    contact_email: Mapped[str | None] = mapped_column(String)
    contact_phone: Mapped[str | None] = mapped_column(String)
    country: Mapped[str | None] = mapped_column(String)
    region: Mapped[str | None] = mapped_column(String)

    products: Mapped[list[Product]] = relationship(
        back_populates="supplier", cascade="all, delete-orphan"
    )
