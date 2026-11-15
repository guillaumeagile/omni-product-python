from __future__ import annotations

from dataclasses import dataclass

from omni_product.anemic_model.product import ProductId


@dataclass(frozen=True)
class Quantity:
    value: int


@dataclass(frozen=True)
class Stock:
    value: int


@dataclass(frozen=True)
class Location:
    value: str


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
