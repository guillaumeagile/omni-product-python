from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from omni_product.database import Base


# Équivalents des @Embeddable Java : valeurs portées par les tables de leur contexte (voir dal/).
@dataclass
class Price:
    base: float | None = None
    tax: float | None = None
    tax_rate: float | None = None


@dataclass
class Warehouse:
    location: str | None = None


@dataclass
class RegionSupplier:
    """`Product.Supplier` en Java : fournisseur embarqué, par région."""

    name: str | None = None
    siren: str | None = None
    tva_id: str | None = None


class Product(Base):
    """Contexte Catalog. Les données des autres contextes sont liées par `id` (dal/)."""

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

    supplier_id: Mapped[str | None] = mapped_column(ForeignKey("suppliers.id"))

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
