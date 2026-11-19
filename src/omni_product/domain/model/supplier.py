from dataclasses import dataclass


@dataclass(frozen=True)
class SupplierId:
    value: str


@dataclass(frozen=True)
class Email:
    value: str


@dataclass(frozen=True)
class Phone:
    value: str


@dataclass(frozen=True)
class Country:
    value: str


@dataclass(frozen=True)
class Region:
    value: str


# Identifiants naturels : leur code est leur identité, attribuée hors du système.
@dataclass(frozen=True)
class Siren:
    value: str


@dataclass(frozen=True)
class TvaId:
    value: str


@dataclass(frozen=True)
class RegionSupplier:
    """`Product.Supplier` en Java : fournisseur embarqué, par région."""

    name: str | None = None
    siren: Siren | None = None
    tva_id: TvaId | None = None


# eq=False : égalité par identité, comme les classes déclaratives d'origine.
@dataclass(eq=False)
class Supplier:
    """Contexte Supplier. Les produits le référencent par `supplier_id`, il ne les liste pas."""

    id: SupplierId
    name: str | None = None
    contact_email: Email | None = None
    contact_phone: Phone | None = None
    country: Country | None = None
    region: Region | None = None
