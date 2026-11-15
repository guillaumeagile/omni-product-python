from __future__ import annotations

from dataclasses import dataclass

from omni_product.anemic_model.invariants import require_at_least_zero, require_text
from omni_product.anemic_model.product import ProductId


@dataclass(frozen=True)
class Kilos:
    value: float

    def __post_init__(self) -> None:
        require_at_least_zero(self, self.value)


@dataclass(frozen=True)
class Volume:
    value: str

    def __post_init__(self) -> None:
        require_text(self, self.value)


# Contexte Transport (livraison) : le poids et l'encombrement qui pèsent sur l'expédition.
@dataclass
class ProductTransport:
    """Le transport d'un produit, identifié par le produit lui-même."""

    id: ProductId
    kilos: Kilos | None = None
    volume: Volume | None = None
