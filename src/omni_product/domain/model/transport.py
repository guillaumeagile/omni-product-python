"""Transport : ce qu'il faut savoir du produit pour l'expédier."""

from dataclasses import dataclass

from omni_product.domain.exception.invalid_value import InvalidValue
from omni_product.domain.model.identity import ProductId


@dataclass(frozen=True)
class Weight:
    """En kilogrammes."""

    value: float

    def __post_init__(self) -> None:
        if self.value < 0:
            raise InvalidValue("Weight cannot be negative")


@dataclass(frozen=True)
class Distance:
    """En kilomètres."""

    value: float

    def __post_init__(self) -> None:
        if self.value < 0:
            raise InvalidValue("Distance cannot be negative")


@dataclass(frozen=True)
class CarbonEmission:
    """En kilogrammes d'équivalent CO2."""

    value: float

    def __post_init__(self) -> None:
        if self.value < 0:
            raise InvalidValue("Carbon emission cannot be negative")


@dataclass(frozen=True)
class TransportMode:
    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise InvalidValue("Transport mode is required")


@dataclass(frozen=True)
class Volume:
    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise InvalidValue("Volume is required")


@dataclass(eq=False)
class ProductTransport:
    """Le produit vu du Transport : il partage l'identité du produit."""

    id: ProductId
    kilos: Weight | None = None
    volume: Volume | None = None
