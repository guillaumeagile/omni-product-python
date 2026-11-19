from sqlalchemy.orm import Session

from omni_product.dal import product_dal, supplier_dal
from omni_product.domain.model.product_values import (
    ContactEmail,
    ContactPhone,
    Country,
    Region,
    SupplierId,
    SupplierName,
)
from omni_product.domain.model.supplier import Supplier


class SupplierService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create_supplier(
        self,
        id: str,
        name: str | None,
        contact_email: str | None,
        contact_phone: str | None,
        country: str | None,
        region: str | None,
    ) -> Supplier:
        supplier = Supplier(
            id=SupplierId(id),
            name=None if name is None else SupplierName(name),
            contact_email=None if contact_email is None else ContactEmail(contact_email),
            contact_phone=None if contact_phone is None else ContactPhone(contact_phone),
            country=None if country is None else Country(country),
            region=None if region is None else Region(region),
        )
        return supplier_dal.save(self._session, supplier)

    def get_supplier(self, supplier_id: str) -> Supplier | None:
        return supplier_dal.find_by_id(self._session, supplier_id)

    def get_all_suppliers(self) -> list[Supplier]:
        return supplier_dal.find_all(self._session)

    def get_suppliers_by_product(self, product_id: str) -> list[Supplier]:
        if product_dal.find_by_id(self._session, product_id) is None:
            raise ValueError(f"Product not found: {product_id}")
        return supplier_dal.find_by_product_id(self._session, product_id)

    def get_suppliers_by_country(self, country: str) -> list[Supplier]:
        return supplier_dal.find_by_country(self._session, country)

    def get_suppliers_by_region(self, region: str) -> list[Supplier]:
        return supplier_dal.find_by_region(self._session, region)

    def update_supplier(
        self,
        id: str,
        name: str | None,
        contact_email: str | None,
        contact_phone: str | None,
        country: str | None,
        region: str | None,
    ) -> Supplier:
        supplier = self._get_or_raise(id)
        if name:
            supplier.name = SupplierName(name)
        supplier.contact_email = None if contact_email is None else ContactEmail(contact_email)
        supplier.contact_phone = None if contact_phone is None else ContactPhone(contact_phone)
        supplier.country = None if country is None else Country(country)
        supplier.region = None if region is None else Region(region)
        return supplier_dal.save(self._session, supplier)

    def delete_supplier(self, supplier_id: str) -> None:
        supplier_dal.delete(self._session, self._get_or_raise(supplier_id))

    def _get_or_raise(self, supplier_id: str) -> Supplier:
        supplier = supplier_dal.find_by_id(self._session, supplier_id)
        if supplier is None:
            raise ValueError(f"Supplier not found: {supplier_id}")
        return supplier
