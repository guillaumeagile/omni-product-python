from dataclasses import dataclass

from omni_product.domain.model.product_values import (
    ContactEmail,
    ContactPhone,
    Country,
    Region,
    SupplierId,
    SupplierName,
)


@dataclass(eq=False)
class Supplier:
    """Un fournisseur. Il ne connaît pas ses produits : le lien passe par `ProductSourcing`."""

    id: SupplierId
    name: SupplierName | None = None
    contact_email: ContactEmail | None = None
    contact_phone: ContactPhone | None = None
    country: Country | None = None
    region: Region | None = None
