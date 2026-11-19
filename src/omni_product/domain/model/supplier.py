"""Supplier : le fournisseur et ses coordonnées."""

from dataclasses import dataclass

from omni_product.domain.exception.invalid_value import InvalidValue
from omni_product.domain.model.identity import SupplierId


@dataclass(frozen=True)
class Email:
    value: str

    def __post_init__(self) -> None:
        if "@" not in self.value:
            raise InvalidValue("Email must contain '@'")


@dataclass(frozen=True)
class Phone:
    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise InvalidValue("Phone is required")


@dataclass(frozen=True)
class Country:
    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise InvalidValue("Country is required")


@dataclass(frozen=True)
class Region:
    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise InvalidValue("Region is required")


@dataclass(eq=False)
class Supplier:
    id: SupplierId
    name: str | None = None
    contact_email: Email | None = None
    contact_phone: Phone | None = None
    country: Country | None = None
    region: Region | None = None
