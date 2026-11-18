from __future__ import annotations

from dataclasses import dataclass

from result import Result

from omni_product.domain.model.errors import InvalidValueError
from omni_product.domain.model.invariants import require_text

# Contexte Approvisionnement : le fournisseur lui-même. Les produits qu'il fournit sont liés
# par `ProductSupply`, dans `procurement.py`.


@dataclass(frozen=True)
class SupplierId:
    value: str

    @classmethod
    def of(cls, value: str) -> Result[SupplierId, InvalidValueError]:
        return require_text(cls, value).map(cls)


@dataclass(frozen=True)
class Country:
    value: str

    @classmethod
    def of(cls, value: str) -> Result[Country, InvalidValueError]:
        return require_text(cls, value).map(cls)


@dataclass(frozen=True)
class Region:
    value: str

    @classmethod
    def of(cls, value: str) -> Result[Region, InvalidValueError]:
        return require_text(cls, value).map(cls)


@dataclass(frozen=True)
class ContactEmail:
    value: str

    @classmethod
    def of(cls, value: str) -> Result[ContactEmail, InvalidValueError]:
        return require_text(cls, value).map(cls)


@dataclass(frozen=True)
class ContactPhone:
    value: str

    @classmethod
    def of(cls, value: str) -> Result[ContactPhone, InvalidValueError]:
        return require_text(cls, value).map(cls)


@dataclass
class Supplier:
    id: SupplierId
    name: str | None = None
    contact_email: ContactEmail | None = None
    contact_phone: ContactPhone | None = None
    country: Country | None = None
    region: Region | None = None
