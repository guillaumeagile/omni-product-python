from __future__ import annotations

from dataclasses import dataclass

from omni_product.anemic_model.product import ProductId


@dataclass(frozen=True)
class Amount:
    value: float


@dataclass(frozen=True)
class Rate:
    value: float


@dataclass(frozen=True)
class Discount:
    value: str


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
