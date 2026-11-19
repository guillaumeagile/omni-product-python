from dataclasses import dataclass


@dataclass(frozen=True)
class TransportMode:
    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise ValueError("Transport mode is required")


@dataclass(frozen=True)
class Distance:
    value: float


@dataclass(frozen=True)
class Weight:
    value: float


@dataclass(frozen=True)
class Co2Kg:
    value: float
