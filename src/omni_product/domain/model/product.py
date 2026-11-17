from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from omni_product.domain.model.invariants import require_at_least_zero, require_text

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


@dataclass(frozen=True)
class ShelfLifeDays:
    value: int

    def __post_init__(self) -> None:
        require_at_least_zero(self, self.value)


@dataclass(frozen=True)
class Perishable:
    """Produit périssable : une date limite, et une durée de conservation."""

    expiration_date: date | None = None
    shelf_life_days: ShelfLifeDays | None = None


@dataclass(frozen=True)
class NonExpiring:
    """Produit sans date limite."""


ShelfLife = Perishable | NonExpiring


@dataclass
class Product:
    id: ProductId
    name: str
    slug: Slug
    images: tuple[ProductImage, ...] = ()
    # Absent : produit standard, sans information de conservation.
    shelf_life: ShelfLife | None = None

    def is_perishable(self) -> bool:
        return isinstance(self.shelf_life, Perishable)
