from dataclasses import dataclass


@dataclass
class Price:
    base: float | None = None
    tax: float | None = None
    tax_rate: float | None = None


@dataclass
class ProductPrice:
    """Le prix d'un produit, rattaché par son identifiant."""

    product_id: str
    price: Price | None = None
