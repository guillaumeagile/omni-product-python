from dataclasses import dataclass

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from omni_product.database import Base


@dataclass(frozen=True)
class Price:
    base: float | None = None
    tax: float | None = None
    tax_rate: float | None = None


@dataclass(frozen=True)
class Pricing:
    price: Price | None
    discounts: tuple[str, ...]


class ProductDiscount(Base):
    __tablename__ = "product_discounts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"))
    discount: Mapped[str] = mapped_column(String)

    def __init__(self, discount: str) -> None:
        self.discount = discount
