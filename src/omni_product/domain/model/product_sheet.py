from __future__ import annotations

from dataclasses import dataclass

from omni_product.domain.model.pricing import ProductPrice
from omni_product.domain.model.procurement import ProductSupply
from omni_product.domain.model.product import Product
from omni_product.domain.model.storage import ProductStock
from omni_product.domain.model.transport import ProductTransport


@dataclass
class ProductSheet:
    """La fiche d'un produit : le Catalogue et les données des autres contextes, assemblés.

    Chaque contexte reste un objet du modèle, identifié par le produit. La fiche ne sert qu'à lire
    et écrire l'ensemble d'un coup, comme l'API le fait.
    """

    product: Product
    pricing: ProductPrice | None = None
    transport: ProductTransport | None = None
    stock: ProductStock | None = None
    supply: ProductSupply | None = None
