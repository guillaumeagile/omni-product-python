from typing import Protocol

from omni_product.domain.model.supplier import Supplier, SupplierId


class SupplierRepository(Protocol):
    """Les fournisseurs, tels que le métier les lit et les écrit."""

    def find_all(self) -> list[Supplier]: ...

    def find_by_id(self, supplier_id: SupplierId) -> Supplier | None: ...

    def save(self, supplier: Supplier) -> Supplier: ...

    def delete(self, supplier: Supplier) -> None: ...
