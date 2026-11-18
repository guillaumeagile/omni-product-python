from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeIs, get_args

from result import Err, Ok, Result

from omni_product.domain.model.errors import InvalidValueError
from omni_product.domain.model.invariants import require_at_least_zero, require_text
from omni_product.domain.model.product import ProductId

# Liste fermée des modes de transport : l'union de littéraux, relue au runtime par `get_args`.
TransportModeName = Literal["truck", "train", "ship", "plane"]
TRANSPORT_MODES: tuple[str, ...] = get_args(TransportModeName)


def _is_transport_mode(value: str) -> TypeIs[TransportModeName]:
    return value in TRANSPORT_MODES


@dataclass(frozen=True)
class TransportMode:
    """Le mode de transport, pris dans la liste fermée `TransportModeName`."""

    value: TransportModeName

    @classmethod
    def of(cls, raw: str) -> Result[TransportMode, InvalidValueError]:
        if not _is_transport_mode(raw):
            return Err(
                InvalidValueError(f"TransportMode doit être l'un de : {', '.join(TRANSPORT_MODES)}")
            )
        return Ok(cls(raw))


@dataclass(frozen=True)
class Distance:
    """Une distance en kilomètres, jamais négative."""

    value: float

    @classmethod
    def of(cls, value: float) -> Result[Distance, InvalidValueError]:
        return require_at_least_zero(cls, value).map(cls)


@dataclass(frozen=True)
class Kilos:
    value: float

    @classmethod
    def of(cls, value: float) -> Result[Kilos, InvalidValueError]:
        return require_at_least_zero(cls, value).map(cls)


@dataclass(frozen=True)
class CarbonKilos:
    """Une quantité de CO2 en kilogrammes, jamais négative."""

    value: float

    @classmethod
    def of(cls, value: float) -> Result[CarbonKilos, InvalidValueError]:
        return require_at_least_zero(cls, value).map(cls)


@dataclass(frozen=True)
class Volume:
    value: str

    @classmethod
    def of(cls, value: str) -> Result[Volume, InvalidValueError]:
        return require_text(cls, value).map(cls)


# Contexte Transport (livraison) : le poids et l'encombrement qui pèsent sur l'expédition.
@dataclass
class ProductTransport:
    """Le transport d'un produit, identifié par le produit lui-même."""

    id: ProductId
    kilos: Kilos | None = None
    volume: Volume | None = None
