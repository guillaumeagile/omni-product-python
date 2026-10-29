import pytest

from omni_product.model import Product
from omni_product.repository.product_repository import ProductRepository
from omni_product.repository.supplier_repository import SupplierRepository
from omni_product.service.supplier_service import SupplierService


@pytest.fixture
def supplier_service(
    supplier_repository: SupplierRepository, product_repository: ProductRepository
) -> SupplierService:
    return SupplierService(supplier_repository, product_repository)


def _create(
    service: SupplierService,
    supplier_id: str,
    name: str,
    country: str = "France",
    region: str = "Île-de-France",
) -> None:
    service.create_supplier(supplier_id, name, "contact@test.com", "+33123456789", country, region)


def test_should_create_supplier(supplier_service: SupplierService) -> None:
    supplier = supplier_service.create_supplier(
        "sup1", "Supplier A", "contact@suppliera.com", "+33123456789", "France", "Île-de-France"
    )

    assert supplier.id == "sup1"
    assert supplier.name == "Supplier A"
    assert supplier.country == "France"


def test_should_get_supplier_by_id(supplier_service: SupplierService) -> None:
    _create(supplier_service, "sup1", "Supplier A")

    found = supplier_service.get_supplier("sup1")

    assert found is not None
    assert found.id == "sup1"
    assert found.name == "Supplier A"


def test_should_return_none_for_non_existent_supplier(supplier_service: SupplierService) -> None:
    assert supplier_service.get_supplier("nonexistent") is None


def test_should_get_all_suppliers(supplier_service: SupplierService) -> None:
    _create(supplier_service, "sup1", "Supplier A")
    _create(supplier_service, "sup2", "Supplier B", "Spain", "Madrid")

    names = [s.name for s in supplier_service.get_all_suppliers()]

    assert names == ["Supplier A", "Supplier B"]


def test_should_get_suppliers_by_country(supplier_service: SupplierService) -> None:
    _create(supplier_service, "sup1", "Supplier A")
    _create(supplier_service, "sup2", "Supplier B", "Spain", "Madrid")

    french = supplier_service.get_suppliers_by_country("France")

    assert [s.name for s in french] == ["Supplier A"]


def test_should_get_suppliers_by_region(supplier_service: SupplierService) -> None:
    _create(supplier_service, "sup1", "Supplier A")
    _create(supplier_service, "sup2", "Supplier B", region="Provence")

    idf = supplier_service.get_suppliers_by_region("Île-de-France")

    assert [s.name for s in idf] == ["Supplier A"]


def test_should_update_supplier(supplier_service: SupplierService) -> None:
    _create(supplier_service, "sup1", "Supplier A")

    updated = supplier_service.update_supplier(
        "sup1", "Updated Supplier A", "newemail@suppliera.com", "+33111111111", "Germany", "Berlin"
    )

    assert updated.name == "Updated Supplier A"
    assert updated.country == "Germany"
    assert updated.region == "Berlin"


def test_should_raise_when_updating_non_existent_supplier(
    supplier_service: SupplierService,
) -> None:
    with pytest.raises(ValueError, match="Supplier not found"):
        supplier_service.update_supplier(
            "nonexistent", "Name", "e@test.com", "+33", "France", "IDF"
        )


def test_should_delete_supplier(supplier_service: SupplierService) -> None:
    _create(supplier_service, "sup1", "Supplier A")

    supplier_service.delete_supplier("sup1")

    assert supplier_service.get_supplier("sup1") is None


def test_should_raise_when_deleting_non_existent_supplier(
    supplier_service: SupplierService,
) -> None:
    with pytest.raises(ValueError, match="Supplier not found"):
        supplier_service.delete_supplier("nonexistent")


def test_should_cascade_delete_products_when_supplier_deleted(
    supplier_service: SupplierService, product_repository: ProductRepository
) -> None:
    _create(supplier_service, "sup1", "Supplier A")
    product_repository.save(
        Product(id="prod1", name="Test Product", slug="test-product", supplier_id="sup1")
    )
    assert product_repository.find_by_id("prod1") is not None

    supplier_service.delete_supplier("sup1")

    assert product_repository.find_by_id("prod1") is None


def test_should_get_suppliers_by_product(
    supplier_service: SupplierService, product_repository: ProductRepository
) -> None:
    """Désactivé en Java (LAZY_LOADING_ISSUE.md) : une requête SQL évite le lazy loading."""
    _create(supplier_service, "sup1", "Supplier A")
    _create(supplier_service, "sup2", "Supplier B")
    product_repository.save(
        Product(id="prod1", name="Test Product", slug="test-product", supplier_id="sup1")
    )

    suppliers = supplier_service.get_suppliers_by_product("prod1")

    assert [s.id for s in suppliers] == ["sup1"]


def test_should_raise_when_getting_suppliers_of_unknown_product(
    supplier_service: SupplierService,
) -> None:
    with pytest.raises(ValueError, match="Product not found"):
        supplier_service.get_suppliers_by_product("ghost")
