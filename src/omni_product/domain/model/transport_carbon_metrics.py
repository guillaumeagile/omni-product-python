from dataclasses import dataclass

from omni_product.domain.model.transport_values import (
    CarbonEmission,
    Distance,
    TransportMode,
    Weight,
)


@dataclass(frozen=True)
class TransportCarbonMetrics:
    carbon_equivalent: CarbonEmission
    direct_carbon: CarbonEmission | None
    transport_mode: TransportMode
    distance: Distance
    weight: Weight

    def __post_init__(self) -> None:
        if (
            self.carbon_equivalent.value < 0
            or self.distance.value < 0
            or self.weight.value < 0
        ):
            raise ValueError("Carbon metrics cannot be negative")
