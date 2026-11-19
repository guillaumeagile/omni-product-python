from dataclasses import dataclass


@dataclass
class Supplier:
    id: str
    name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    country: str | None = None
    region: str | None = None
