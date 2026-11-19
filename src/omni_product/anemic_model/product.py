from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm.collections import attribute_keyed_dict

from omni_product.database import Base

_ROW_CASCADE = "all, delete-orphan"


# Équivalent des @ElementCollection + @CollectionTable.
class ProductImage(Base):
    __tablename__ = "product_images"

    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), primary_key=True)
    image_key: Mapped[str] = mapped_column(String, primary_key=True)
    image_detail: Mapped[str | None] = mapped_column(String)

    def __init__(self, image_key: str, image_detail: str | None) -> None:
        self.image_key = image_key
        self.image_detail = image_detail


class Product(Base):
    """Le produit tel que le catalogue le voit. Les autres contextes le retrouvent par `id`."""

    __tablename__ = "products"
    # Héritage mono-table : toutes les sous-classes partagent la table `products`.
    __mapper_args__ = {  # noqa: RUF012
        "polymorphic_on": "kind",
        "polymorphic_identity": "standard",
    }

    id: Mapped[str] = mapped_column(String, primary_key=True)
    kind: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    image_rows: Mapped[dict[str, ProductImage]] = relationship(
        collection_class=attribute_keyed_dict("image_key"), cascade=_ROW_CASCADE
    )
    images: AssociationProxy[dict[str, str | None]] = association_proxy(
        "image_rows", "image_detail", creator=ProductImage
    )

    def is_perishable(self) -> bool:
        # La classe de base connaît sa sous-classe : une branche de plus à chaque nouveau type.
        return isinstance(self, PerishableProduct)


class PerishableProduct(Product):
    """Produit périssable. Ses colonnes sont dans `products`, donc nulles pour les autres types."""

    __mapper_args__ = {"polymorphic_identity": "perishable"}  # noqa: RUF012

    expiration_date: Mapped[date | None] = mapped_column(Date)
    shelf_life_days: Mapped[int | None] = mapped_column(Integer)


class NonExpiringProduct(Product):
    """Produit sans date limite. Aucun champ propre : la classe ne sert qu'à porter un type."""

    __mapper_args__ = {"polymorphic_identity": "non_expiring"}  # noqa: RUF012
