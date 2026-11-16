from dataclasses import dataclass

from omni_product.domain.model.transport import Distance, Kilos, TransportMode


@dataclass(frozen=True)
class TransportCarbonMetrics:
    co2_equivalent_kg: float
    co2_direct_kg: float | None
    transport_mode: TransportMode
    distance: Distance
    weight: Kilos

    def __post_init__(self) -> None:
        if self.co2_equivalent_kg < 0:
            raise ValueError("Carbon metrics cannot be negative")
