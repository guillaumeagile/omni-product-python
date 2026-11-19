from dataclasses import dataclass


@dataclass
class Warehouse:
    location: str | None = None


@dataclass
class ProductStock:
    """Le stock d'un produit, rattaché par l'identifiant du produit."""

    product_id: str
    quantity: int | None = None
    stock: int | None = None
    warehouse: Warehouse | None = None
