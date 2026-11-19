from dataclasses import dataclass


@dataclass(frozen=True)
class Location:
    value: str


# Équivalent du @Embeddable Java : valeur portée par la table de son contexte (voir dal/).
@dataclass(frozen=True)
class Warehouse:
    location: Location | None = None
