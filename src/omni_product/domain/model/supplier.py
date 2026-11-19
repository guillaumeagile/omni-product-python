from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from omni_product.domain.model.product import Product


@dataclass
class Supplier:
    id: str
    name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    country: str | None = None
    region: str | None = None
    products: list[Product] = field(default_factory=list)
