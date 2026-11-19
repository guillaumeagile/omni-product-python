"""Pricing : le prix d'un produit et ses remises."""

from dataclasses import dataclass, field

from omni_product.domain.exception.invalid_value import InvalidValue
from omni_product.domain.model.identity import ProductId


@dataclass(frozen=True)
class Amount:
    value: float

    def __post_init__(self) -> None:
        if self.value < 0:
            raise InvalidValue("Amount cannot be negative")


@dataclass(frozen=True)
class TaxRate:
    value: float

    def __post_init__(self) -> None:
        if not 0 <= self.value <= 1:
            raise InvalidValue("Tax rate must be between 0 and 1")


@dataclass(frozen=True)
class Price:
    base: Amount | None = None
    tax: Amount | None = None
    tax_rate: TaxRate | None = None


@dataclass(eq=False)
class ProductPricing:
    """Le produit vu du Pricing : il partage l'identité du produit."""

    id: ProductId
    price: Price = field(default_factory=Price)
    discounts: list[str] = field(default_factory=list[str])
