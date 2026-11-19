from dataclasses import dataclass

from omni_product.domain.model.product import ProductId


@dataclass(frozen=True)
class Kilos:
    value: float


@dataclass(frozen=True)
class Volume:
    value: str


@dataclass
class ProductShipment:
    """L'expédition d'un produit : poids et volume, rattachés par l'identifiant du produit."""

    id: ProductId
    kilos: Kilos | None = None
    volume: Volume | None = None
