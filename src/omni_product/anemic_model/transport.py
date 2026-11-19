from dataclasses import dataclass


@dataclass(frozen=True)
class Transport:
    kilos: float | None = None
    volume: str | None = None
