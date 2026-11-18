from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from result import Result

from omni_product.domain.model.errors import ErreurProduit
from omni_product.domain.model.invariants import require_at_least_zero, require_text

# Contexte Catalogue : le produit, ses images et ses types. Les autres contextes (prix, transport,
# stockage, approvisionnement) ont leurs propres classes, reliées au produit par son identifiant.


@dataclass(frozen=True)
class ProductId:
    value: str

    @classmethod
    def of(cls, value: str) -> Result[ProductId, ErreurProduit]:
        return require_text(cls, value, ErreurProduit).map(cls)


@dataclass(frozen=True)
class Slug:
    value: str

    @classmethod
    def of(cls, value: str) -> Result[Slug, ErreurProduit]:
        return require_text(cls, value, ErreurProduit).map(cls)


@dataclass(frozen=True)
class ImageKey:
    value: str

    @classmethod
    def of(cls, value: str) -> Result[ImageKey, ErreurProduit]:
        return require_text(cls, value, ErreurProduit).map(cls)


@dataclass(frozen=True)
class ImageDetail:
    value: str

    @classmethod
    def of(cls, value: str) -> Result[ImageDetail, ErreurProduit]:
        return require_text(cls, value, ErreurProduit).map(cls)


@dataclass(frozen=True)
class ProductImage:
    key: ImageKey
    detail: ImageDetail | None = None


@dataclass(frozen=True)
class ShelfLifeDays:
    value: int

    @classmethod
    def of(cls, value: int) -> Result[ShelfLifeDays, ErreurProduit]:
        return require_at_least_zero(cls, value, ErreurProduit).map(cls)


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
