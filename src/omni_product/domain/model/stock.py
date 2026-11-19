from dataclasses import dataclass

from omni_product.domain.model.product import ProductId


@dataclass(frozen=True)
class Quantity:
    value: int


@dataclass(frozen=True)
class Stock:
    value: int


@dataclass(frozen=True)
class WarehouseLocation:
    value: str


@dataclass(frozen=True)
class Warehouse:
    location: WarehouseLocation | None = None


@dataclass
class ProductStock:
    """Le stock d'un produit, rattaché par l'identifiant du produit."""

    id: ProductId
    quantity: Quantity | None = None
    stock: Stock | None = None
    warehouse: Warehouse | None = None
