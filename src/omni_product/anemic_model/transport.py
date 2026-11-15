from __future__ import annotations

from dataclasses import dataclass

from omni_product.anemic_model.product import ProductId


@dataclass(frozen=True)
class Kilos:
    value: float


@dataclass(frozen=True)
class Volume:
    value: str


# Contexte Transport (livraison) : le poids et l'encombrement qui pèsent sur l'expédition.
@dataclass
class ProductTransport:
    """Le transport d'un produit, identifié par le produit lui-même."""

    id: ProductId
    kilos: Kilos | None = None
    volume: Volume | None = None
