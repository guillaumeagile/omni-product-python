from dataclasses import dataclass
from datetime import date

from omni_product.domain.model.supplier import SupplierId


@dataclass(frozen=True)
class ProductId:
    value: str


@dataclass(frozen=True)
class Slug:
    value: str


@dataclass(frozen=True)
class ShelfLifeDays:
    value: int


@dataclass(frozen=True)
class Perishable:
    """Produit périssable : ses dates sont portées par la variante, pas par `Product`."""

    expiration_date: date | None = None
    shelf_life_days: ShelfLifeDays | None = None


@dataclass(frozen=True)
class NonExpiring:
    """Produit sans date limite. Aucun champ propre : la valeur ne sert qu'à porter la variante."""


type ShelfLife = Perishable | NonExpiring


# eq=False : égalité par identité, comme les classes déclaratives d'origine.
@dataclass(eq=False)
class Product:
    """Contexte Catalog. Les données des autres contextes sont liées par `id` (dal/).

    `shelf_life` à None : produit « standard », sans notion de péremption.
    """

    id: ProductId
    name: str
    slug: Slug
    supplier_id: SupplierId | None = None
    shelf_life: ShelfLife | None = None

    def is_perishable(self) -> bool:
        match self.shelf_life:
            case Perishable():
                return True
            case NonExpiring() | None:
                return False
