from __future__ import annotations

from dataclasses import dataclass
from datetime import date


# Équivalents des @Embeddable Java : valeurs portées par les tables de leur contexte (voir dal/).
@dataclass(frozen=True)
class Price:
    base: float | None = None
    tax: float | None = None
    tax_rate: float | None = None


@dataclass(frozen=True)
class Warehouse:
    location: str | None = None


@dataclass(frozen=True)
class RegionSupplier:
    """`Product.Supplier` en Java : fournisseur embarqué, par région."""

    name: str | None = None
    siren: str | None = None
    tva_id: str | None = None


# eq=False : égalité par identité, comme les classes déclaratives d'origine.
@dataclass(eq=False)
class Product:
    """Contexte Catalog. Les données des autres contextes sont liées par `id` (dal/)."""

    id: str
    name: str
    slug: str
    supplier_id: str | None = None

    def is_perishable(self) -> bool:
        # La classe de base connaît sa sous-classe : une branche de plus à chaque nouveau type.
        return isinstance(self, PerishableProduct)


@dataclass(eq=False)
class PerishableProduct(Product):
    """Produit périssable. Ses colonnes sont dans `products`, donc nulles pour les autres types."""

    expiration_date: date | None = None
    shelf_life_days: int | None = None


class NonExpiringProduct(Product):
    """Produit sans date limite. Aucun champ propre : la classe ne sert qu'à porter un type."""
