import pytest

from omni_product.controller import supplier_controller as controller
from omni_product.domain.model import Product, ProductId, ProductSupply, Slug
from omni_product.infrastructure.persistence.in_memory import (
    InMemoryRepository,
    InMemorySupplierRepository,
)
from omni_product.service.supplier_service import SupplierService


@pytest.fixture
def service(
    suppliers: InMemorySupplierRepository,
    products: InMemoryRepository[Product],
    supplies: InMemoryRepository[ProductSupply],
) -> SupplierService:
    return SupplierService(suppliers, products, supplies)


def test_should_create_supplier_with_201(service: SupplierService) -> None:
    assert controller.create_supplier(service, "sup1", "Supplier A") == (
        201,
        {"id": "sup1", "name": "Supplier A"},
    )


def test_should_answer_422_when_supplier_id_is_empty(service: SupplierService) -> None:
    statut, corps = controller.create_supplier(service, "", "Supplier A")

    assert statut == 422
    assert isinstance(corps, dict)
    assert "detail" in corps


def test_should_get_existing_supplier_with_200(service: SupplierService) -> None:
    controller.create_supplier(service, "sup1", "Supplier A")

    assert controller.get_supplier(service, "sup1") == (200, {"id": "sup1", "name": "Supplier A"})


def test_should_answer_404_when_supplier_is_unknown(service: SupplierService) -> None:
    assert controller.get_supplier(service, "nonexistent")[0] == 404
    assert controller.update_supplier(service, "nonexistent", "Name")[0] == 404
    assert controller.delete_supplier(service, "nonexistent")[0] == 404


def test_should_update_supplier_with_200(service: SupplierService) -> None:
    controller.create_supplier(service, "sup1", "Supplier A")

    assert controller.update_supplier(service, "sup1", "Renamed") == (
        200,
        {"id": "sup1", "name": "Renamed"},
    )


def test_should_delete_supplier_with_204(service: SupplierService) -> None:
    controller.create_supplier(service, "sup1", "Supplier A")

    assert controller.delete_supplier(service, "sup1") == (204, None)
    assert controller.get_supplier(service, "sup1")[0] == 404


def test_should_answer_404_when_product_is_unknown(service: SupplierService) -> None:
    assert controller.get_suppliers_by_product(service, "ghost")[0] == 404


def test_should_list_suppliers_of_known_product(
    service: SupplierService,
    products: InMemoryRepository[Product],
) -> None:
    controller.create_supplier(service, "sup1", "Supplier A")
    products.save(Product(id=ProductId("prod1"), name="Test Product", slug=Slug("test-product")))

    assert controller.get_suppliers_by_product(service, "prod1") == (200, [])
