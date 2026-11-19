"""Transport : ce qu'il faut savoir du produit pour l'expédier."""

from dataclasses import dataclass


@dataclass(eq=False)
class ProductTransport:
    product_id: str
    kilos: float | None = None
    volume: str | None = None
