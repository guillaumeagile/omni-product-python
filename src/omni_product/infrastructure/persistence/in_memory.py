from copy import deepcopy
from typing import Protocol

from omni_product.domain.model import ProductId, Supplier, SupplierId


class _IdentifiedByProduct(Protocol):
    @property
    def id(self) -> ProductId: ...


class InMemoryRepository[T: _IdentifiedByProduct]:
    """Implémente `ContextRepository` en mémoire. Copie en entrée et en sortie."""

    def __init__(self) -> None:
        self._items: dict[ProductId, T] = {}

    def find_all(self) -> list[T]:
        ids = sorted(self._items, key=lambda product_id: product_id.value)
        return [deepcopy(self._items[product_id]) for product_id in ids]

    def find_by_id(self, product_id: ProductId) -> T | None:
        return deepcopy(self._items.get(product_id))

    def save(self, aggregate: T) -> T:
        self._items[aggregate.id] = deepcopy(aggregate)
        return deepcopy(aggregate)

    def delete_by_id(self, product_id: ProductId) -> None:
        self._items.pop(product_id, None)


class InMemorySupplierRepository:
    """Implémente `SupplierRepository` en mémoire."""

    def __init__(self) -> None:
        self._suppliers: dict[SupplierId, Supplier] = {}

    def find_all(self) -> list[Supplier]:
        ids = sorted(self._suppliers, key=lambda supplier_id: supplier_id.value)
        return [deepcopy(self._suppliers[supplier_id]) for supplier_id in ids]

    def find_by_id(self, supplier_id: SupplierId) -> Supplier | None:
        return deepcopy(self._suppliers.get(supplier_id))

    def save(self, supplier: Supplier) -> Supplier:
        self._suppliers[supplier.id] = deepcopy(supplier)
        return deepcopy(supplier)

    def delete(self, supplier: Supplier) -> None:
        self._suppliers.pop(supplier.id, None)
