"""Value Objects et identifiants du modèle produit et fournisseur.

Un identifiant est un type dédié (ProductId, pas str). Une valeur est un dataclass figé.
"""

from dataclasses import dataclass
from datetime import date

# --- Identifiants d'entité ---------------------------------------------------------------------


@dataclass(frozen=True)
class ProductId:
    value: str


@dataclass(frozen=True)
class SupplierId:
    value: str


@dataclass(frozen=True)
class DiscountId:
    value: int


@dataclass(frozen=True)
class ImageRowId:
    value: int


@dataclass(frozen=True)
class RegionRowId:
    value: int


# --- Contexte Catalog --------------------------------------------------------------------------


@dataclass(frozen=True)
class ProductName:
    value: str


@dataclass(frozen=True)
class Slug:
    value: str


@dataclass(frozen=True)
class ImageKey:
    value: str


@dataclass(frozen=True)
class ImageDetail:
    value: str


@dataclass(frozen=True)
class ExpirationDate:
    value: date


@dataclass(frozen=True)
class ShelfLifeDays:
    value: int


# --- Contexte Pricing --------------------------------------------------------------------------


@dataclass(frozen=True)
class Amount:
    value: float


@dataclass(frozen=True)
class TaxRate:
    value: float


@dataclass(frozen=True)
class Discount:
    value: str


# --- Contexte Storage --------------------------------------------------------------------------


@dataclass(frozen=True)
class Quantity:
    value: int


@dataclass(frozen=True)
class Stock:
    value: int


@dataclass(frozen=True)
class WarehouseLocation:
    value: str


# --- Contexte Transport ------------------------------------------------------------------------


@dataclass(frozen=True)
class Kilos:
    value: float


@dataclass(frozen=True)
class Volume:
    value: str


# --- Contexte Supplier -------------------------------------------------------------------------


@dataclass(frozen=True)
class Region:
    value: str


@dataclass(frozen=True)
class SupplierName:
    value: str


@dataclass(frozen=True)
class Siren:
    value: str


@dataclass(frozen=True)
class TvaId:
    value: str


@dataclass(frozen=True)
class ContactEmail:
    value: str


@dataclass(frozen=True)
class ContactPhone:
    value: str


@dataclass(frozen=True)
class Country:
    value: str
