"""Storage : ce qu'on a en stock, et où."""

from dataclasses import dataclass, field


@dataclass
class Warehouse:
    location: str | None = None


@dataclass(eq=False)
class ProductStorage:
    product_id: str
    quantity: int | None = None
    stock: int | None = None
    warehouse: Warehouse = field(default_factory=Warehouse)
