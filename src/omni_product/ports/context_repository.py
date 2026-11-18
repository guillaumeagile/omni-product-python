from typing import Protocol

from omni_product.kernel.ids import ProductId


class ContextRepository[T](Protocol):
    """Les agrégats d'un contexte, identifiés par le produit : catalogue, approvisionnement..."""

    def find_all(self) -> list[T]: ...

    def find_by_id(self, product_id: ProductId) -> T | None: ...

    def save(self, aggregate: T) -> T: ...

    def delete_by_id(self, product_id: ProductId) -> None: ...
