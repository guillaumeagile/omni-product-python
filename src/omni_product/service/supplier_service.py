from omni_product.model import Supplier
from omni_product.repository.product_repository import ProductRepository
from omni_product.repository.supplier_repository import SupplierRepository


class SupplierService:
    def __init__(
        self, supplier_repository: SupplierRepository, product_repository: ProductRepository
    ) -> None:
        self._supplier_repository = supplier_repository
        self._product_repository = product_repository

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
        return self._supplier_repository.save(supplier)

    def get_supplier(self, supplier_id: str) -> Supplier | None:
        return self._supplier_repository.find_by_id(supplier_id)

    def get_all_suppliers(self) -> list[Supplier]:
        return self._supplier_repository.find_all()

    def get_suppliers_by_product(self, product_id: str) -> list[Supplier]:
        if self._product_repository.find_by_id(product_id) is None:
            raise ValueError(f"Product not found: {product_id}")
        return self._supplier_repository.find_by_product_id(product_id)

    def get_suppliers_by_country(self, country: str) -> list[Supplier]:
        return self._supplier_repository.find_by_country(country)

    def get_suppliers_by_region(self, region: str) -> list[Supplier]:
        return self._supplier_repository.find_by_region(region)

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
        return self._supplier_repository.save(supplier)

    def delete_supplier(self, supplier_id: str) -> None:
        self._supplier_repository.delete(self._get_or_raise(supplier_id))

    def _get_or_raise(self, supplier_id: str) -> Supplier:
        supplier = self._supplier_repository.find_by_id(supplier_id)
        if supplier is None:
            raise ValueError(f"Supplier not found: {supplier_id}")
        return supplier
