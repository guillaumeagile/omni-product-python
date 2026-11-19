from dataclasses import dataclass

from omni_product.domain.exception.invalid_value import InvalidValue
from omni_product.domain.model.transport import Distance, TransportMode, Weight


@dataclass(frozen=True)
class TransportRequest:
    """Le mode vide et les valeurs négatives sont refusés par les Value Objects ; zéro, ici."""

    transport_mode: TransportMode
    distance_km: Distance
    weight_kg: Weight

    def __post_init__(self) -> None:
        if self.distance_km.value == 0:
            raise InvalidValue("Distance must be positive")
        if self.weight_kg.value == 0:
            raise InvalidValue("Weight must be positive")
