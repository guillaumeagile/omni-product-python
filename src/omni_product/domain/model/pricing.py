from __future__ import annotations

from dataclasses import dataclass

from result import Result

from omni_product.domain.model.errors import InvalidValueError
from omni_product.domain.model.invariants import require_at_least_zero, require_rate, require_text
from omni_product.domain.model.product import ProductId


@dataclass(frozen=True)
class Amount:
    value: float

    @classmethod
    def of(cls, value: float) -> Result[Amount, InvalidValueError]:
        return require_at_least_zero(cls, value).map(cls)


@dataclass(frozen=True)
class Rate:
    value: float

    @classmethod
    def of(cls, value: float) -> Result[Rate, InvalidValueError]:
        return require_rate(cls, value).map(cls)


@dataclass(frozen=True)
class Discount:
    value: str

    @classmethod
    def of(cls, value: str) -> Result[Discount, InvalidValueError]:
        return require_text(cls, value).map(cls)


# Contexte Pricing : ce que coûte un produit, et les remises qui s'y appliquent.
@dataclass(frozen=True)
class Price:
    base: Amount | None = None
    tax: Amount | None = None
    tax_rate: Rate | None = None


@dataclass
class ProductPrice:
    """Le prix d'un produit, identifié par le produit lui-même."""

    id: ProductId
    price: Price | None = None
    discounts: tuple[Discount, ...] = ()
