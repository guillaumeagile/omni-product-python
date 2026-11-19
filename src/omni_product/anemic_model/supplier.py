from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from omni_product.database import Base


class Supplier(Base):
    """Contexte Supplier. Les produits le référencent par `supplier_id`, il ne les liste pas."""

    __tablename__ = "suppliers"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str | None] = mapped_column(String)
    contact_email: Mapped[str | None] = mapped_column(String)
    contact_phone: Mapped[str | None] = mapped_column(String)
    country: Mapped[str | None] = mapped_column(String)
    region: Mapped[str | None] = mapped_column(String)
