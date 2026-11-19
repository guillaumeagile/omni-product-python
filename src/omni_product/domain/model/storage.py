"""Storage : ce qu'on a en stock, et où."""

from dataclasses import dataclass, field

from omni_product.domain.exception.invalid_value import InvalidValue
from omni_product.domain.model.identity import ProductId


@dataclass(frozen=True)
class Quantity:
    value: int

    def __post_init__(self) -> None:
        if self.value < 0:
            raise InvalidValue("Quantity cannot be negative")


@dataclass(frozen=True)
class Location:
    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise InvalidValue("Location is required")


@dataclass(frozen=True)
class Warehouse:
    location: Location | None = None


@dataclass(eq=False)
class ProductStorage:
    """Le produit vu du Storage : il partage l'identité du produit."""

    id: ProductId
    quantity: Quantity | None = None
    stock: Quantity | None = None
    warehouse: Warehouse = field(default_factory=Warehouse)
