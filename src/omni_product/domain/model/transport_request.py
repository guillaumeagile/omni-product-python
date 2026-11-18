from dataclasses import dataclass


@dataclass(frozen=True)
class TransportRequest:
    transport_mode: str
    distance_km: float
    weight_kg: float

    def __post_init__(self) -> None:
        if not self.transport_mode or not self.transport_mode.strip():
            raise ValueError("Transport mode is required")
        if self.distance_km is None or self.distance_km <= 0:  # pyright: ignore[reportUnnecessaryComparison]
            raise ValueError("Distance must be positive")
        if self.weight_kg is None or self.weight_kg <= 0:  # pyright: ignore[reportUnnecessaryComparison]
            raise ValueError("Weight must be positive")
