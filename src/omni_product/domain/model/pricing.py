"""Pricing : le prix d'un produit et ses remises."""

from dataclasses import dataclass, field


@dataclass
class Price:
    base: float | None = None
    tax: float | None = None
    tax_rate: float | None = None


@dataclass(eq=False)
class ProductPricing:
    product_id: str
    price: Price = field(default_factory=Price)
    discounts: list[str] = field(default_factory=list[str])
