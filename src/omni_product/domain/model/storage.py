from __future__ import annotations

from dataclasses import dataclass

from result import Result

from omni_product.domain.model.product import ProductId
from omni_product.kernel.errors import ErreurStock
from omni_product.kernel.invariants import require_at_least_zero, require_text


@dataclass(frozen=True)
class Quantity:
    value: int

    @classmethod
    def of(cls, value: int) -> Result[Quantity, ErreurStock]:
        return require_at_least_zero(cls, value, ErreurStock).map(cls)


@dataclass(frozen=True)
class Stock:
    value: int

    @classmethod
    def of(cls, value: int) -> Result[Stock, ErreurStock]:
        return require_at_least_zero(cls, value, ErreurStock).map(cls)


@dataclass(frozen=True)
class Location:
    value: str

    @classmethod
    def of(cls, value: str) -> Result[Location, ErreurStock]:
        return require_text(cls, value, ErreurStock).map(cls)


# Contexte Stockage : combien d'unités existent, et où elles sont rangées.
@dataclass(frozen=True)
class Warehouse:
    location: Location | None = None


@dataclass
class ProductStock:
    """Le stock d'un produit, identifié par le produit lui-même.

    La quantité est toujours connue : sans quantité saisie, l'appelant prend le stock.
    """

    id: ProductId
    quantity: Quantity
    stock: Stock
    warehouse: Warehouse | None = None
