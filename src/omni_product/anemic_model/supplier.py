from __future__ import annotations

from dataclasses import dataclass

# Contexte Approvisionnement : le fournisseur lui-même. Les produits qu'il fournit sont liés
# par `ProductSupply`, dans `procurement.py`.


@dataclass(frozen=True)
class SupplierId:
    value: str


@dataclass(frozen=True)
class Country:
    value: str


@dataclass(frozen=True)
class Region:
    value: str


@dataclass(frozen=True)
class ContactEmail:
    value: str


@dataclass(frozen=True)
class ContactPhone:
    value: str


@dataclass
class Supplier:
    id: SupplierId
    name: str | None = None
    contact_email: ContactEmail | None = None
    contact_phone: ContactPhone | None = None
    country: Country | None = None
    region: Region | None = None
