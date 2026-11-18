from result import Err, Ok, Result
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
from omni_product.domain.model.errors import InvalidValueError
from omni_product.domain.model.invariants import optionnel, premiere_erreur


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
    ) -> Result[Supplier, InvalidValueError]:
        erreur = premiere_erreur(
            [
                SupplierId.of(id),
                optionnel(ContactEmail.of, contact_email),
                optionnel(ContactPhone.of, contact_phone),
                optionnel(Country.of, country),
                optionnel(Region.of, region),
            ]
        )
        if erreur is not None:
            return Err(erreur)
        supplier = Supplier(
            id=SupplierId(id),
            name=name,
            contact_email=optional(ContactEmail, contact_email),
            contact_phone=optional(ContactPhone, contact_phone),
            country=optional(Country, country),
            region=optional(Region, region),
        )
        return Ok(supplier_dal.save(self._session, supplier))

    def get_supplier(self, supplier_id: str) -> Result[Supplier | None, InvalidValueError]:
        return SupplierId.of(supplier_id).map(self._find_by_id)

    def get_all_suppliers(self) -> list[Supplier]:
        return supplier_dal.find_all(self._session)

    def get_suppliers_by_product(
        self, product_id: str
    ) -> Result[list[Supplier], InvalidValueError]:
        return ProductId.of(product_id).map(self._suppliers_of_existing_product)

    def get_suppliers_by_country(self, country: str) -> Result[list[Supplier], InvalidValueError]:
        return Country.of(country).map(self._suppliers_of_country)

    def get_suppliers_by_region(self, region: str) -> Result[list[Supplier], InvalidValueError]:
        return Region.of(region).map(self._suppliers_of_region)

    def update_supplier(
        self,
        id: str,
        name: str | None,
        contact_email: str | None,
        contact_phone: str | None,
        country: str | None,
        region: str | None,
    ) -> Result[Supplier, InvalidValueError]:
        erreur = premiere_erreur(
            [
                SupplierId.of(id),
                optionnel(ContactEmail.of, contact_email),
                optionnel(ContactPhone.of, contact_phone),
                optionnel(Country.of, country),
                optionnel(Region.of, region),
            ]
        )
        if erreur is not None:
            return Err(erreur)
        supplier = self._get_or_raise(SupplierId(id))
        supplier.name = name or supplier.name
        supplier.contact_email = optional(ContactEmail, contact_email)
        supplier.contact_phone = optional(ContactPhone, contact_phone)
        supplier.country = optional(Country, country)
        supplier.region = optional(Region, region)
        return Ok(supplier_dal.save(self._session, supplier))

    def delete_supplier(self, supplier_id: str) -> Result[None, InvalidValueError]:
        return SupplierId.of(supplier_id).map(self._delete)

    def _find_by_id(self, supplier_id: SupplierId) -> Supplier | None:
        return supplier_dal.find_by_id(self._session, supplier_id)

    def _suppliers_of_country(self, country: Country) -> list[Supplier]:
        return supplier_dal.find_by_country(self._session, country)

    def _suppliers_of_region(self, region: Region) -> list[Supplier]:
        return supplier_dal.find_by_region(self._session, region)

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
