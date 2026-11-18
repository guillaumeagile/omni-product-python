from __future__ import annotations

from dataclasses import dataclass

from result import Err, Ok, Result

from omni_product.domain.model.errors import ErreurTarification
from omni_product.domain.model.invariants import require_at_least_zero, require_rate, require_text
from omni_product.domain.model.product import ProductId


@dataclass(frozen=True)
class Amount:
    value: float

    @classmethod
    def of(cls, value: float) -> Result[Amount, ErreurTarification]:
        return require_at_least_zero(cls, value, ErreurTarification).map(cls)


@dataclass(frozen=True)
class Rate:
    value: float

    @classmethod
    def of(cls, value: float) -> Result[Rate, ErreurTarification]:
        return require_rate(cls, value, ErreurTarification).map(cls)


@dataclass(frozen=True)
class Discount:
    value: str

    @classmethod
    def of(cls, value: str) -> Result[Discount, ErreurTarification]:
        return require_text(cls, value, ErreurTarification).map(cls)


# Contexte Pricing : ce que coûte un produit, et les remises qui s'y appliquent.
@dataclass(frozen=True)
class PrixHorsTaxe:
    """Un prix de base, sans taxe."""

    base: Amount


@dataclass(frozen=True)
class PrixAvecTaxe:
    """Un prix de base, avec sa taxe et le taux qui la produit."""

    base: Amount
    tax: Amount
    tax_rate: Rate


Price = PrixHorsTaxe | PrixAvecTaxe


def prix_of(
    base: float | None, tax: float | None, tax_rate: float | None
) -> Result[Price | None, ErreurTarification]:
    """Le prix que décrivent les trois valeurs, ou `None` si aucune n'est donnée.

    Une taxe demande à la fois son montant et son taux, et un prix de base.
    """
    if base is None:
        if tax is None and tax_rate is None:
            return Ok(None)
        return Err(ErreurTarification("Une taxe demande un prix de base"))
    match Amount.of(base):
        case Err(erreur):
            return Err(erreur)
        case Ok(montant):
            if tax is None and tax_rate is None:
                return Ok(PrixHorsTaxe(montant))
            if tax is None or tax_rate is None:
                return Err(ErreurTarification("Une taxe demande son montant et son taux"))
            return _prix_avec_taxe(montant, tax, tax_rate)


def _prix_avec_taxe(
    montant: Amount, tax: float, tax_rate: float
) -> Result[Price, ErreurTarification]:
    match (Amount.of(tax), Rate.of(tax_rate)):
        case (Ok(taxe), Ok(taux)):
            return Ok(PrixAvecTaxe(montant, taxe, taux))
        case (Err(erreur), _):
            return Err(erreur)
        case (_, Err(erreur)):
            return Err(erreur)


@dataclass
class ProductPrice:
    """Le prix d'un produit, identifié par le produit lui-même."""

    id: ProductId
    price: Price | None = None
    discounts: tuple[Discount, ...] = ()
