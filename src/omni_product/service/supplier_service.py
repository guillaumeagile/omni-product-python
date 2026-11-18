from result import Err, Ok, Result
from sqlalchemy.orm import Session

from omni_product.dal import product_dal, supplier_dal
from omni_product.domain.model import ProductId, Supplier, SupplierId
from omni_product.domain.model.errors import InvalidValueError


class SupplierService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create_supplier(self, id: str, name: str) -> Result[Supplier, InvalidValueError]:
        match SupplierId.of(id):
            case Err(erreur):
                return Err(erreur)
            case Ok(supplier_id):
                supplier = Supplier(id=supplier_id, name=name)
                return Ok(supplier_dal.save(self._session, supplier))

    def get_supplier(self, supplier_id: str) -> Result[Supplier | None, InvalidValueError]:
        return SupplierId.of(supplier_id).map(self._find_by_id)

    def get_all_suppliers(self) -> list[Supplier]:
        return supplier_dal.find_all(self._session)

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
                return Ok(supplier_dal.save(self._session, supplier))

    def delete_supplier(self, supplier_id: str) -> Result[None, InvalidValueError]:
        return SupplierId.of(supplier_id).map(self._delete)

    def _find_by_id(self, supplier_id: SupplierId) -> Supplier | None:
        return supplier_dal.find_by_id(self._session, supplier_id)

    def _delete(self, supplier_id: SupplierId) -> None:
        supplier_dal.delete(self._session, self._get_or_raise(supplier_id))

    def _suppliers_of_existing_product(self, product: ProductId) -> list[Supplier]:
        if product_dal.find_by_id(self._session, product) is None:
            raise ValueError(f"Product not found: {product.value}")
        return supplier_dal.find_by_product_id(self._session, product)

    def _get_or_raise(self, supplier_id: SupplierId) -> Supplier:
        supplier = self._find_by_id(supplier_id)
        if supplier is None:
            raise ValueError(f"Supplier not found: {supplier_id.value}")
        return supplier
