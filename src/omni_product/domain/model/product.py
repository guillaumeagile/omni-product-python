"""Catalog : la fiche du produit. Les autres contextes s'y relient par `ProductId`."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from omni_product.domain.exception.invalid_value import InvalidValue
from omni_product.domain.model.identity import ProductId


@dataclass(frozen=True)
class Slug:
    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise InvalidValue("Slug is required")


@dataclass(frozen=True)
class ShelfLifeDays:
    value: int

    def __post_init__(self) -> None:
        if self.value < 0:
            raise InvalidValue("Shelf life cannot be negative")


@dataclass(eq=False)
class Product:
    id: ProductId
    name: str
    slug: Slug
    images: dict[str, str | None] = field(default_factory=dict[str, str | None])

    def is_perishable(self) -> bool:
        # La classe de base connaît sa sous-classe : une branche de plus à chaque nouveau type.
        return isinstance(self, PerishableProduct)


@dataclass(eq=False)
class PerishableProduct(Product):
    """Produit périssable."""

    expiration_date: date | None = None
    shelf_life_days: ShelfLifeDays | None = None


@dataclass(eq=False)
class NonExpiringProduct(Product):
    """Produit sans date limite. Aucun champ propre : la classe ne sert qu'à porter un type."""
