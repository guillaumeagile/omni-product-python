from dataclasses import dataclass

from omni_product.domain.model.transport import Distance, Kilos, TransportMode


@dataclass(frozen=True)
class TransportRequest:
    transport_mode: TransportMode
    distance_km: Distance
    weight_kg: Kilos

    def __post_init__(self) -> None:
        if self.distance_km.value <= 0:
            raise ValueError("Distance must be positive")
        if self.weight_kg.value <= 0:
            raise ValueError("Weight must be positive")
