from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from result import Err, Ok, Result

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
class ParDateLimite:
    """Produit périssable daté : une date limite, sans durée de conservation."""

    expiration_date: date


@dataclass(frozen=True)
class ParDureeDeConservation:
    """Produit périssable : une durée de conservation, sans date limite."""

    shelf_life_days: ShelfLifeDays


@dataclass(frozen=True)
class ParDateEtDuree:
    """Produit périssable avec sa date limite et sa durée de conservation."""

    expiration_date: date
    shelf_life_days: ShelfLifeDays


# Une variante par combinaison légale des deux informations : au moins l'une des deux.
Perishable = ParDateLimite | ParDureeDeConservation | ParDateEtDuree


@dataclass(frozen=True)
class NonExpiring:
    """Produit sans date limite."""


ShelfLife = Perishable | NonExpiring


def date_limite(shelf_life: ShelfLife | None) -> date | None:
    """La date limite du produit, si sa durée de vie en porte une."""
    match shelf_life:
        case ParDateLimite(expiration_date=limite) | ParDateEtDuree(expiration_date=limite):
            return limite
        case _:
            return None


def perissable_of(
    expiration_date: date | None, shelf_life_days: int | None
) -> Result[Perishable, ErreurProduit]:
    """Le produit périssable que décrivent la date limite et la durée : au moins l'une des deux."""
    if shelf_life_days is None:
        if expiration_date is None:
            return Err(ErreurProduit("Un produit périssable a une date limite ou une durée"))
        return Ok(ParDateLimite(expiration_date))
    match ShelfLifeDays.of(shelf_life_days):
        case Err(erreur):
            return Err(erreur)
        case Ok(duree):
            if expiration_date is None:
                return Ok(ParDureeDeConservation(duree))
            return Ok(ParDateEtDuree(expiration_date, duree))


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
