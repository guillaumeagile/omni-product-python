from sqlalchemy.orm import Session

from omni_product.dal import product_dal, supplier_dal
from omni_product.domain.model.product import ProductId
from omni_product.domain.model.supplier import (
    Country,
    Email,
    Phone,
    Region,
    Supplier,
    SupplierId,
)
from omni_product.service.product_service import ProductService


class SupplierService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create_supplier(
        self,
        id: SupplierId,
        name: str | None,
        contact_email: Email | None,
        contact_phone: Phone | None,
        country: Country | None,
        region: Region | None,
    ) -> Supplier:
        supplier = Supplier(
            id=id,
            name=name,
            contact_email=contact_email,
            contact_phone=contact_phone,
            country=country,
            region=region,
        )
        return supplier_dal.save(self._session, supplier)

    def get_supplier(self, supplier_id: SupplierId) -> Supplier | None:
        return supplier_dal.find_by_id(self._session, supplier_id)

    def get_all_suppliers(self) -> list[Supplier]:
        return supplier_dal.find_all(self._session)

    def get_suppliers_by_product(self, product_id: ProductId) -> list[Supplier]:
        if product_dal.find_by_id(self._session, product_id) is None:
            raise ValueError(f"Product not found: {product_id.value}")
        return supplier_dal.find_by_product_id(self._session, product_id)

    def get_suppliers_by_country(self, country: Country) -> list[Supplier]:
        return supplier_dal.find_by_country(self._session, country)

    def get_suppliers_by_region(self, region: Region) -> list[Supplier]:
        return supplier_dal.find_by_region(self._session, region)

    def update_supplier(
        self,
        id: SupplierId,
        name: str | None,
        contact_email: Email | None,
        contact_phone: Phone | None,
        country: Country | None,
        region: Region | None,
    ) -> Supplier:
        supplier = self._get_or_raise(id)
        supplier.name = name or supplier.name
        supplier.contact_email = contact_email
        supplier.contact_phone = contact_phone
        supplier.country = country
        supplier.region = region
        return supplier_dal.save(self._session, supplier)

    def delete_supplier(self, supplier_id: SupplierId) -> None:
        supplier = self._get_or_raise(supplier_id)
        ProductService(self._session).delete_by_supplier_id(supplier_id)
        supplier_dal.delete(self._session, supplier)

    def from_services(self, id: SupplierId, name: str) -> Supplier:
        """Fournisseur neuf, avec sa région connue. Sans liste de produits (contexte Catalog)."""
        supplier = Supplier(id=id, name=name)
        existing = self.get_supplier(id)
        supplier.region = existing.region if existing is not None else None
        return supplier

    def _get_or_raise(self, supplier_id: SupplierId) -> Supplier:
        supplier = supplier_dal.find_by_id(self._session, supplier_id)
        if supplier is None:
            raise ValueError(f"Supplier not found: {supplier_id.value}")
        return supplier
