from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Integer, String
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm.collections import attribute_keyed_dict

from omni_product.anemic_model.catalog import ProductImage
from omni_product.database import Base

_ROW_CASCADE = "all, delete-orphan"


class Product(Base):
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
