from dataclasses import dataclass, field
from datetime import date


@dataclass
class Product:
    id: str
    name: str
    slug: str
    supplier_id: str | None = None
    images: dict[str, str | None] = field(default_factory=lambda: dict[str, str | None]())

    def is_perishable(self) -> bool:
        return isinstance(self, PerishableProduct)


@dataclass
class PerishableProduct(Product):
    """Produit périssable."""

    expiration_date: date | None = None
    shelf_life_days: int | None = None


@dataclass
class NonExpiringProduct(Product):
    """Produit sans date limite. Aucun champ propre : la classe ne sert qu'à porter un type."""
