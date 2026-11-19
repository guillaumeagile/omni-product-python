from dataclasses import dataclass


@dataclass(frozen=True)
class TransportMode:
    value: str


@dataclass(frozen=True)
class Distance:
    value: float


@dataclass(frozen=True)
class Weight:
    value: float


@dataclass(frozen=True)
class CarbonEmission:
    value: float
