from typing import Protocol

from omni_product.domain.model.product import ProductId
from omni_product.domain.model.product_sheet import ProductSheet


class ProductRepository(Protocol):
    """Le catalogue des fiches produit, tel que le métier le lit et l'écrit."""

    def find_all(self) -> list[ProductSheet]: ...

    def find_by_id(self, product_id: ProductId) -> ProductSheet | None: ...

    def save(self, sheet: ProductSheet) -> ProductSheet: ...

    def delete_by_id(self, product_id: ProductId) -> None: ...
