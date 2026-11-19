from dataclasses import dataclass

from omni_product.anemic_model import (
    Product,
    ProductPricing,
    ProductStorage,
    ProductSupply,
    ProductTransport,
)


@dataclass(frozen=True)
class ProductSheet:
    """La fiche complète d'un produit : ce que chaque contexte en sait, réuni pour l'API."""

    product: Product
    pricing: ProductPricing
    storage: ProductStorage
    transport: ProductTransport
    supply: ProductSupply
