from __future__ import annotations

from dataclasses import dataclass

from omni_product.anemic_model import (
    Product,
    ProductPrice,
    ProductShipment,
    ProductStock,
    ProductSupply,
)


@dataclass(frozen=True)
class ProductView:
    """Un produit tel qu'un écran le lit : un agrégat par contexte, reliés par `product_id`.

    C'est une projection de lecture, composée par le service. Elle ne se persiste pas :
    chaque agrégat se sauvegarde seul. Un agrégat absent (`None`) veut dire que le contexte
    n'a rien renseigné pour ce produit.
    """

    product: Product
    price: ProductPrice | None = None
    shipment: ProductShipment | None = None
    stock: ProductStock | None = None
    supply: ProductSupply | None = None
