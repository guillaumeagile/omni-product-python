from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from omni_product.domain.model.invariants import require_text

# Contexte Catalogue : le produit, ses images et ses types. Les autres contextes (prix, transport,
# stockage, approvisionnement) ont leurs propres classes, reliées au produit par son identifiant.


@dataclass(frozen=True)
class ProductId:
    value: str

    def __post_init__(self) -> None:
        require_text(self, self.value)


@dataclass(frozen=True)
class Slug:
    value: str

    def __post_init__(self) -> None:
        require_text(self, self.value)


@dataclass(frozen=True)
class ImageKey:
    value: str

    def __post_init__(self) -> None:
        require_text(self, self.value)


@dataclass(frozen=True)
class ImageDetail:
    value: str

    def __post_init__(self) -> None:
        require_text(self, self.value)


@dataclass(frozen=True)
class ProductImage:
    key: ImageKey
    detail: ImageDetail | None = None


@dataclass
class Product:
    id: ProductId
    name: str
    slug: Slug
    images: tuple[ProductImage, ...] = ()

    def is_perishable(self) -> bool:
        # La classe de base connaît sa sous-classe : une branche de plus à chaque nouveau type.
        return isinstance(self, PerishableProduct)


@dataclass
class PerishableProduct(Product):
    """Produit périssable : une date limite, et une durée de conservation."""

    expiration_date: date | None = None
    shelf_life_days: int | None = None


@dataclass
class NonExpiringProduct(Product):
    """Produit sans date limite. Aucun champ propre : la classe ne sert qu'à porter un type."""
