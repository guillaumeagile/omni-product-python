from typing import Protocol

from omni_product.kernel.ids import SupplierId


class SupplierRepository[T](Protocol):
    """Les fournisseurs, tels que le métier les lit et les écrit. `T` est l'entité fournisseur."""

    def find_all(self) -> list[T]: ...

    def find_by_id(self, supplier_id: SupplierId) -> T | None: ...

    def save(self, supplier: T) -> T: ...

    def delete(self, supplier: T) -> None: ...
