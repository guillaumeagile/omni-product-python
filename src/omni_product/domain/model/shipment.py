from dataclasses import dataclass


@dataclass
class ProductShipment:
    """L'expédition d'un produit : poids et volume, rattachés par l'identifiant du produit."""

    product_id: str
    kilos: float | None = None
    volume: str | None = None
