from dataclasses import dataclass

from omni_product.domain.model.product import ProductId


@dataclass(frozen=True)
class BasePrice:
    value: float


@dataclass(frozen=True)
class TaxAmount:
    value: float


@dataclass(frozen=True)
class TaxRate:
    value: float


@dataclass(frozen=True)
class Price:
    base: BasePrice | None = None
    tax: TaxAmount | None = None
    tax_rate: TaxRate | None = None


@dataclass
class ProductPrice:
    """Le prix d'un produit, rattaché par son identifiant."""

    id: ProductId
    price: Price | None = None
