from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class ProductId:
    value: str


@dataclass(frozen=True)
class Slug:
    value: str


@dataclass(frozen=True)
class ShelfLifeDays:
    value: int


@dataclass
class Product:
    id: ProductId
    name: str
    slug: Slug
    supplier_id: str | None = None
    images: dict[str, str | None] = field(default_factory=lambda: dict[str, str | None]())

    def is_perishable(self) -> bool:
        return isinstance(self, PerishableProduct)


@dataclass
class PerishableProduct(Product):
    """Produit périssable."""

    expiration_date: date | None = None
    shelf_life_days: ShelfLifeDays | None = None


@dataclass
class NonExpiringProduct(Product):
    """Produit sans date limite. Aucun champ propre : la classe ne sert qu'à porter un type."""
