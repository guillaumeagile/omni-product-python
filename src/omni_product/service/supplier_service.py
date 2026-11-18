from result import Err, Ok, Result

from omni_product.domain.model import ProductId, Supplier, SupplierId
from omni_product.domain.model.errors import InvalidValueError
from omni_product.domain.port.product_repository import ProductRepository
from omni_product.domain.port.supplier_repository import SupplierRepository


class SupplierService:
    """Le cas d'usage des fournisseurs. Il ne connaît que les ports de persistance."""

    def __init__(self, suppliers: SupplierRepository, products: ProductRepository) -> None:
        self._suppliers = suppliers
        self._products = products

    def create_supplier(self, id: str, name: str) -> Result[Supplier, InvalidValueError]:
        match SupplierId.of(id):
            case Err(erreur):
                return Err(erreur)
            case Ok(supplier_id):
                supplier = Supplier(id=supplier_id, name=name)
                return Ok(self._suppliers.save(supplier))

    def get_supplier(self, supplier_id: str) -> Result[Supplier | None, InvalidValueError]:
        return SupplierId.of(supplier_id).map(self._suppliers.find_by_id)

    def get_all_suppliers(self) -> list[Supplier]:
        return self._suppliers.find_all()

    def get_suppliers_by_product(
        self, product_id: str
    ) -> Result[list[Supplier], InvalidValueError]:
        return ProductId.of(product_id).map(self._suppliers_of_existing_product)

    def update_supplier(self, id: str, name: str | None) -> Result[Supplier, InvalidValueError]:
        match SupplierId.of(id):
            case Err(erreur):
                return Err(erreur)
            case Ok(supplier_id):
                supplier = self._get_or_raise(supplier_id)
                supplier.name = name or supplier.name
                return Ok(self._suppliers.save(supplier))

    def delete_supplier(self, supplier_id: str) -> Result[None, InvalidValueError]:
        return SupplierId.of(supplier_id).map(self._delete)

    def _delete(self, supplier_id: SupplierId) -> None:
        self._suppliers.delete(self._get_or_raise(supplier_id))

    def _suppliers_of_existing_product(self, product: ProductId) -> list[Supplier]:
        if self._products.find_by_id(product) is None:
            raise ValueError(f"Product not found: {product.value}")
        return self._suppliers.find_by_product_id(product)

    def _get_or_raise(self, supplier_id: SupplierId) -> Supplier:
        supplier = self._suppliers.find_by_id(supplier_id)
        if supplier is None:
            raise ValueError(f"Supplier not found: {supplier_id.value}")
        return supplier
