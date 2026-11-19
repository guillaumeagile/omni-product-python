"""Catalog : la fiche du produit. Les autres contextes s'y relient par `product_id`."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass(eq=False)
class Product:
    id: str
    name: str
    slug: str
    images: dict[str, str | None] = field(default_factory=dict[str, str | None])

    def is_perishable(self) -> bool:
        # La classe de base connaît sa sous-classe : une branche de plus à chaque nouveau type.
        return isinstance(self, PerishableProduct)


@dataclass(eq=False)
class PerishableProduct(Product):
    """Produit périssable."""

    expiration_date: date | None = None
    shelf_life_days: int | None = None


@dataclass(eq=False)
class NonExpiringProduct(Product):
    """Produit sans date limite. Aucun champ propre : la classe ne sert qu'à porter un type."""
