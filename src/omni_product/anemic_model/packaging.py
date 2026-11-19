from dataclasses import dataclass


@dataclass(frozen=True)
class Packaging:
    volume: str | None = None
