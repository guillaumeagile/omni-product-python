from __future__ import annotations

from dataclasses import dataclass

from result import Err, Ok, Result

from omni_product.domain.model.errors import ErreurTransport
from omni_product.domain.model.invariants import require_at_least_zero, require_text
from omni_product.domain.model.product import ProductId


@dataclass(frozen=True)
class Kilos:
    value: float

    @classmethod
    def of(cls, value: float) -> Result[Kilos, ErreurTransport]:
        return require_at_least_zero(cls, value, ErreurTransport).map(cls)


@dataclass(frozen=True)
class Volume:
    value: str

    @classmethod
    def of(cls, value: str) -> Result[Volume, ErreurTransport]:
        return require_text(cls, value, ErreurTransport).map(cls)


# Contexte Transport (livraison) : le poids et l'encombrement qui pèsent sur l'expédition.
@dataclass(frozen=True)
class Charge:
    """Le poids et le volume d'un produit : tous deux, ou aucun."""

    kilos: Kilos
    volume: Volume


@dataclass
class ProductTransport:
    """Le transport d'un produit, identifié par le produit lui-même."""

    id: ProductId
    kilos_volume: Charge | None = None


def charge_of(kilos: float | None, volume: str | None) -> Result[Charge | None, ErreurTransport]:
    """La charge que décrivent le poids et le volume : tous deux, ou aucun."""
    if kilos is None and volume is None:
        return Ok(None)
    if kilos is None or volume is None:
        return Err(ErreurTransport("Le poids et le volume vont ensemble"))
    return _charge(kilos, volume)


def _charge(kilos: float, volume: str) -> Result[Charge, ErreurTransport]:
    match (Kilos.of(kilos), Volume.of(volume)):
        case (Ok(poids), Ok(encombrement)):
            return Ok(Charge(poids, encombrement))
        case (Err(erreur), _):
            return Err(erreur)
        case (_, Err(erreur)):
            return Err(erreur)
