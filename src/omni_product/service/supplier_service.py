from sqlalchemy.orm import Session

from omni_product.dal import product_dal, supplier_dal
from omni_product.dal.records import optional
from omni_product.domain.model import (
    ContactEmail,
    ContactPhone,
    Country,
    ProductId,
    Region,
    Supplier,
    SupplierId,
)


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
            name=name,
            contact_email=optional(ContactEmail, contact_email),
            contact_phone=optional(ContactPhone, contact_phone),
            country=optional(Country, country),
            region=optional(Region, region),
        )
        return supplier_dal.save(self._session, supplier)

    def get_supplier(self, supplier_id: str) -> Supplier | None:
        return supplier_dal.find_by_id(self._session, SupplierId(supplier_id))

    def get_all_suppliers(self) -> list[Supplier]:
        return supplier_dal.find_all(self._session)

    def get_suppliers_by_product(self, product_id: str) -> list[Supplier]:
        product = ProductId(product_id)
        if product_dal.find_by_id(self._session, product) is None:
            raise ValueError(f"Product not found: {product_id}")
        return supplier_dal.find_by_product_id(self._session, product)

    def get_suppliers_by_country(self, country: str) -> list[Supplier]:
        return supplier_dal.find_by_country(self._session, Country(country))

    def get_suppliers_by_region(self, region: str) -> list[Supplier]:
        return supplier_dal.find_by_region(self._session, Region(region))

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
        supplier.name = name or supplier.name
        supplier.contact_email = optional(ContactEmail, contact_email)
        supplier.contact_phone = optional(ContactPhone, contact_phone)
        supplier.country = optional(Country, country)
        supplier.region = optional(Region, region)
        return supplier_dal.save(self._session, supplier)

    def delete_supplier(self, supplier_id: str) -> None:
        supplier_dal.delete(self._session, self._get_or_raise(supplier_id))

    def _get_or_raise(self, supplier_id: str) -> Supplier:
        supplier = supplier_dal.find_by_id(self._session, SupplierId(supplier_id))
        if supplier is None:
            raise ValueError(f"Supplier not found: {supplier_id}")
        return supplier
