from __future__ import annotations

from dataclasses import dataclass

from omni_product.domain.model.invariants import require_at_least_zero, require_text
from omni_product.domain.model.product import ProductId


@dataclass(frozen=True)
class Quantity:
    value: int

    def __post_init__(self) -> None:
        require_at_least_zero(self, self.value)


@dataclass(frozen=True)
class Stock:
    value: int

    def __post_init__(self) -> None:
        require_at_least_zero(self, self.value)


@dataclass(frozen=True)
class Location:
    value: str

    def __post_init__(self) -> None:
        require_text(self, self.value)


# Contexte Stockage : combien d'unités existent, et où elles sont rangées.
@dataclass(frozen=True)
class Warehouse:
    location: Location | None = None


@dataclass
class ProductStock:
    """Le stock d'un produit, identifié par le produit lui-même."""

    id: ProductId
    quantity: Quantity | None = None
    stock: Stock | None = None
    warehouse: Warehouse | None = None
