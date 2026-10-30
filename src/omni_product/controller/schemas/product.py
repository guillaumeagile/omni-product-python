from datetime import date
from typing import Literal

from omni_product.controller.schemas.base import CamelModel

ProductKind = Literal["standard", "perishable", "non_expiring"]


class PriceSchema(CamelModel):
    base: float | None = None
    tax: float | None = None
    tax_rate: float | None = None


class WarehouseSchema(CamelModel):
    location: str | None = None


class RegionSupplierSchema(CamelModel):
    name: str | None = None
    siren: str | None = None
    tva_id: str | None = None


class ProductSchema(CamelModel):
    id: str | None = None
    kind: ProductKind | None = None
    name: str | None = None
    slug: str | None = None
    price: PriceSchema | None = None
    discounts: list[str] | None = None
    images: dict[str, str | None] | None = None
    suppliers_regions: dict[str, RegionSupplierSchema] | None = None
    kilos: float | None = None
    volume: str | None = None
    quantity: int | None = None
    stock: int | None = None
    warehouse: WarehouseSchema | None = None
    supplier_id: str | None = None
    # Champs de PerishableProduct, à plat : le client doit savoir lesquels ont un sens pour `kind`.
    expiration_date: date | None = None
    shelf_life_days: int | None = None
