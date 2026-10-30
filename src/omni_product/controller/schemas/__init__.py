"""Contrats HTTP (DTO) et conversion vers le modèle.

- `base` : la sérialisation commune (camelCase JSON).
- `product` / `supplier` : les DTO, sans logique.
- `mapping` : la conversion entre DTO et entités, seul endroit qui teste le type d'un produit.
"""

from omni_product.controller.schemas.base import CamelModel
from omni_product.controller.schemas.mapping import (
    product_to_schema,
    schema_to_product,
    supplier_to_schema,
)
from omni_product.controller.schemas.product import (
    PriceSchema,
    ProductKind,
    ProductSchema,
    RegionSupplierSchema,
    WarehouseSchema,
)
from omni_product.controller.schemas.supplier import (
    SupplierRequest,
    SupplierSchema,
    SupplierUpdateRequest,
)

__all__ = [
    "CamelModel",
    "PriceSchema",
    "ProductKind",
    "ProductSchema",
    "RegionSupplierSchema",
    "SupplierRequest",
    "SupplierSchema",
    "SupplierUpdateRequest",
    "WarehouseSchema",
    "product_to_schema",
    "schema_to_product",
    "supplier_to_schema",
]
