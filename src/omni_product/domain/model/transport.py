from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeIs, get_args

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
    def parse(cls, raw: str) -> TransportMode:
        if not _is_transport_mode(raw):
            raise ValueError(f"TransportMode doit être l'un de : {', '.join(TRANSPORT_MODES)}")
        return cls(raw)


@dataclass(frozen=True)
class Distance:
    """Une distance en kilomètres, jamais négative."""

    value: float

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("Distance cannot be negative")


@dataclass(frozen=True)
class Kilos:
    """Une masse en kilogrammes, jamais négative."""

    value: float

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("Kilos cannot be negative")


@dataclass(frozen=True)
class CarbonKilos:
    """Une masse de CO2 en kilogrammes, jamais négative."""

    value: float

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("Carbon cannot be negative")
