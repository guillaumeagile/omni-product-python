from dataclasses import dataclass

from omni_product.domain.model.transport_values import Distance, TransportMode, Weight


@dataclass(frozen=True)
class TransportRequest:
    transport_mode: TransportMode
    distance_km: Distance
    weight_kg: Weight

    def __post_init__(self) -> None:
        if self.distance_km.value <= 0:
            raise ValueError("Distance must be positive")
        if self.weight_kg.value <= 0:
            raise ValueError("Weight must be positive")
