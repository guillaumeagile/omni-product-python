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


@dataclass
class Supplier:
    id: SupplierId
    name: str | None = None
    contact_email: Email | None = None
    contact_phone: Phone | None = None
    country: Country | None = None
    region: Region | None = None
