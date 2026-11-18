from __future__ import annotations

from dataclasses import dataclass

from result import Result

from omni_product.domain.model.errors import InvalidValueError
from omni_product.domain.model.invariants import require_at_least_zero, require_text
from omni_product.domain.model.product import ProductId


@dataclass(frozen=True)
class Quantity:
    value: int

    @classmethod
    def of(cls, value: int) -> Result[Quantity, InvalidValueError]:
        return require_at_least_zero(cls, value).map(cls)


@dataclass(frozen=True)
class Stock:
    value: int

    @classmethod
    def of(cls, value: int) -> Result[Stock, InvalidValueError]:
        return require_at_least_zero(cls, value).map(cls)


@dataclass(frozen=True)
class Location:
    value: str

    @classmethod
    def of(cls, value: str) -> Result[Location, InvalidValueError]:
        return require_text(cls, value).map(cls)


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
