from functools import partial

from result import Result

from omni_product.domain.model import Product, ProductId, ProductSupply, Supplier, SupplierId
from omni_product.domain.model.errors import InvalidValueError
from omni_product.domain.port.context_repository import ContextRepository
from omni_product.domain.port.supplier_repository import SupplierRepository


class SupplierService:
    """Le cas d'usage des fournisseurs. L'approvisionnement fait le lien avec les produits."""

    def __init__(
        self,
        suppliers: SupplierRepository,
        products: ContextRepository[Product],
        supplies: ContextRepository[ProductSupply],
    ) -> None:
        self._suppliers = suppliers
        self._products = products
        self._supplies = supplies

    def create_supplier(self, id: str, name: str) -> Result[Supplier, InvalidValueError]:
        return SupplierId.of(id).map(partial(self._create, name=name))

    def _create(self, supplier_id: SupplierId, *, name: str) -> Supplier:
        return self._suppliers.save(Supplier(id=supplier_id, name=name))

    def get_supplier(self, supplier_id: str) -> Result[Supplier | None, InvalidValueError]:
        return SupplierId.of(supplier_id).map(self._suppliers.find_by_id)

    def get_all_suppliers(self) -> list[Supplier]:
        return self._suppliers.find_all()

    def get_suppliers_by_product(
        self, product_id: str
    ) -> Result[list[Supplier], InvalidValueError]:
        return ProductId.of(product_id).map(self._suppliers_of_existing_product)

    def update_supplier(self, id: str, name: str | None) -> Result[Supplier, InvalidValueError]:
        return SupplierId.of(id).map(partial(self._update, name=name))

    def _update(self, supplier_id: SupplierId, *, name: str | None) -> Supplier:
        supplier = self._get_or_raise(supplier_id)
        supplier.name = name or supplier.name
        return self._suppliers.save(supplier)

    def delete_supplier(self, supplier_id: str) -> Result[None, InvalidValueError]:
        return SupplierId.of(supplier_id).map(self._delete)

    def _delete(self, supplier_id: SupplierId) -> None:
        supplier = self._get_or_raise(supplier_id)
        # Comportement conservé : supprimer un fournisseur supprime les produits qu'il fournit.
        for supply in self._supplies.find_all():
            if supply.supplier_id == supplier.id:
                self._products.delete_by_id(supply.id)
                self._supplies.delete_by_id(supply.id)
        self._suppliers.delete(supplier)

    def _suppliers_of_existing_product(self, product: ProductId) -> list[Supplier]:
        if self._products.find_by_id(product) is None:
            raise ValueError(f"Product not found: {product.value}")
        supply = self._supplies.find_by_id(product)
        supplier_id = None if supply is None else supply.supplier_id
        supplier = None if supplier_id is None else self._suppliers.find_by_id(supplier_id)
        return [] if supplier is None else [supplier]

    def _get_or_raise(self, supplier_id: SupplierId) -> Supplier:
        supplier = self._suppliers.find_by_id(supplier_id)
        if supplier is None:
            raise ValueError(f"Supplier not found: {supplier_id.value}")
        return supplier
