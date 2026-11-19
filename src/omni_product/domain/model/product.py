"""Catalog : la fiche du produit. Sa conservation est une variante composée : `ShelfLife`.

Les autres contextes s'y relient par `ProductId`.
"""

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


@dataclass(frozen=True)
class Perishable:
    """Produit périssable : il a (ou aura) une date d'expiration."""

    expiration_date: date | None = None
    shelf_life_days: ShelfLifeDays | None = None


@dataclass(frozen=True)
class NonExpiring:
    """Produit sans date limite."""


type ShelfLife = Perishable | NonExpiring


@dataclass(eq=False)
class Product:
    id: ProductId
    name: str
    slug: Slug
    images: dict[str, str | None] = field(default_factory=dict[str, str | None])
    # Aucune conservation connue : un produit standard.
    shelf_life: ShelfLife | None = None

    def is_perishable(self) -> bool:
        match self.shelf_life:
            case Perishable():
                return True
            case NonExpiring() | None:
                return False
