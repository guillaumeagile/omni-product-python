from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from omni_product.domain.model.supplier import Supplier


@dataclass
class Price:
    base: float | None = None
    tax: float | None = None
    tax_rate: float | None = None


@dataclass
class Warehouse:
    location: str | None = None


@dataclass
class RegionSupplier:
    """Product's supplier embedded by region."""

    name: str | None = None
    siren: str | None = None
    tva_id: str | None = None


@dataclass
class ProductDiscount:
    product_id: str
    discount: str


@dataclass
class ProductImage:
    product_id: str
    image_key: str
    image_detail: str | None = None


@dataclass
class ProductSupplierRegion:
    product_id: str
    region: str
    supplier: RegionSupplier


@dataclass
class Product:
    id: str
    name: str
    slug: str
    price: Price
    kind: str = "standard"
    kilos: float | None = None
    volume: str | None = None
    quantity: int | None = None
    stock: int | None = None
    warehouse: Warehouse = field(default_factory=Warehouse)
    supplier_id: str | None = None
    supplier: Supplier | None = None
    discount_rows: list[ProductDiscount] = field(default_factory=list)
    image_rows: dict[str, ProductImage] = field(default_factory=dict)
    supplier_region_rows: dict[str, ProductSupplierRegion] = field(default_factory=dict)
    discounts: list[str] = field(default_factory=list)
    images: dict[str, str | None] = field(default_factory=dict)
    suppliers_regions: dict[str, RegionSupplier] = field(default_factory=dict)

    def is_perishable(self) -> bool:
        return isinstance(self, PerishableProduct)


@dataclass
class PerishableProduct(Product):
    """Perishable product with expiration tracking."""

    kind: str = "perishable"
    expiration_date: date | None = None
    shelf_life_days: int | None = None


@dataclass
class NonExpiringProduct(Product):
    """Non-expiring product."""

    kind: str = "non_expiring"
