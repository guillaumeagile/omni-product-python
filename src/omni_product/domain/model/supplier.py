from dataclasses import dataclass


# eq=False : égalité par identité, comme les classes déclaratives d'origine.
@dataclass(eq=False)
class Supplier:
    """Contexte Supplier. Les produits le référencent par `supplier_id`, il ne les liste pas."""

    id: str
    name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    country: str | None = None
    region: str | None = None
