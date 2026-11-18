from dataclasses import dataclass


@dataclass(frozen=True)
class TransportCarbonMetrics:
    co2_equivalent_kg: float
    co2_direct_kg: float | None
    transport_mode: str
    distance: float
    weight: float

    def __post_init__(self) -> None:
        if self.co2_equivalent_kg < 0 or self.distance < 0 or self.weight < 0:
            raise ValueError("Carbon metrics cannot be negative")
