from dataclasses import dataclass


@dataclass(frozen=True)
class Warehouse:
    location: str | None = None


@dataclass(frozen=True)
class Storage:
    quantity: int | None
    stock: int | None
    warehouse: Warehouse | None
