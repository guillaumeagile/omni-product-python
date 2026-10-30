from sqlalchemy.orm import Session

from omni_product.dal import product_dal, supplier_dal
from omni_product.model import Supplier


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
            id=id,
            name=name,
            contact_email=contact_email,
            contact_phone=contact_phone,
            country=country,
            region=region,
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
        supplier.name = name
        supplier.contact_email = contact_email
        supplier.contact_phone = contact_phone
        supplier.country = country
        supplier.region = region
        return supplier_dal.save(self._session, supplier)

    def delete_supplier(self, supplier_id: str) -> None:
        supplier_dal.delete(self._session, self._get_or_raise(supplier_id))

    def _get_or_raise(self, supplier_id: str) -> Supplier:
        supplier = supplier_dal.find_by_id(self._session, supplier_id)
        if supplier is None:
            raise ValueError(f"Supplier not found: {supplier_id}")
        return supplier
