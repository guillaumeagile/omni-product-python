from __future__ import annotations

from dataclasses import dataclass

from omni_product.anemic_model.invariants import require_at_least_zero, require_rate, require_text
from omni_product.anemic_model.product import ProductId


@dataclass(frozen=True)
class Amount:
    value: float

    def __post_init__(self) -> None:
        require_at_least_zero(self, self.value)


@dataclass(frozen=True)
class Rate:
    value: float

    def __post_init__(self) -> None:
        require_rate(self, self.value)


@dataclass(frozen=True)
class Discount:
    value: str

    def __post_init__(self) -> None:
        require_text(self, self.value)


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
