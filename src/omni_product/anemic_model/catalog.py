from dataclasses import dataclass

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from omni_product.database import Base


@dataclass(frozen=True)
class CatalogIdentity:
    name: str
    slug: str


@dataclass(frozen=True)
class Catalog:
    identity: CatalogIdentity
    images: dict[str, str | None]


class ProductImage(Base):
    __tablename__ = "product_images"

    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), primary_key=True)
    image_key: Mapped[str] = mapped_column(String, primary_key=True)
    image_detail: Mapped[str | None] = mapped_column(String)

    def __init__(self, image_key: str, image_detail: str | None) -> None:
        self.image_key = image_key
        self.image_detail = image_detail
