import pytest

from omni_product.domain.model import (
    Product,
    ProductId,
    ProductSupply,
    Slug,
    SupplierId,
)
from omni_product.domain.model.product_sheet import ProductSheet
from omni_product.infrastructure.persistence.in_memory import (
    InMemoryProductRepository,
    InMemorySupplierRepository,
)
from omni_product.service.supplier_service import SupplierService


@pytest.fixture
def supplier_service(
    suppliers: InMemorySupplierRepository, products: InMemoryProductRepository
) -> SupplierService:
    return SupplierService(suppliers, products)


def _create(service: SupplierService, supplier_id: str, name: str) -> None:
    service.create_supplier(supplier_id, name).unwrap()


def test_should_create_supplier(supplier_service: SupplierService) -> None:
    supplier = supplier_service.create_supplier("sup1", "Supplier A").unwrap()

    assert supplier.id == SupplierId("sup1")
    assert supplier.name == "Supplier A"


def test_should_get_supplier_by_id(supplier_service: SupplierService) -> None:
    _create(supplier_service, "sup1", "Supplier A")

    found = supplier_service.get_supplier("sup1").unwrap()

    assert found is not None
    assert found.id == SupplierId("sup1")
    assert found.name == "Supplier A"


def test_should_return_none_for_non_existent_supplier(supplier_service: SupplierService) -> None:
    assert supplier_service.get_supplier("nonexistent").unwrap() is None


def test_should_get_all_suppliers(supplier_service: SupplierService) -> None:
    _create(supplier_service, "sup1", "Supplier A")
    _create(supplier_service, "sup2", "Supplier B")

    names = [s.name for s in supplier_service.get_all_suppliers()]

    assert names == ["Supplier A", "Supplier B"]


def test_should_update_supplier(supplier_service: SupplierService) -> None:
    _create(supplier_service, "sup1", "Supplier A")

    updated = supplier_service.update_supplier("sup1", "Updated Supplier A").unwrap()

    assert updated.name == "Updated Supplier A"


def test_should_keep_name_when_update_gives_none(supplier_service: SupplierService) -> None:
    _create(supplier_service, "sup1", "Supplier A")

    updated = supplier_service.update_supplier("sup1", None).unwrap()

    assert updated.name == "Supplier A"


def test_should_raise_when_updating_non_existent_supplier(
    supplier_service: SupplierService,
) -> None:
    with pytest.raises(ValueError, match="Supplier not found"):
        supplier_service.update_supplier("nonexistent", "Name")


def test_should_delete_supplier(supplier_service: SupplierService) -> None:
    _create(supplier_service, "sup1", "Supplier A")

    supplier_service.delete_supplier("sup1").unwrap()

    assert supplier_service.get_supplier("sup1").unwrap() is None


def test_should_raise_when_deleting_non_existent_supplier(
    supplier_service: SupplierService,
) -> None:
    with pytest.raises(ValueError, match="Supplier not found"):
        supplier_service.delete_supplier("nonexistent")


def test_should_cascade_delete_products_when_supplier_deleted(
    supplier_service: SupplierService, products: InMemoryProductRepository
) -> None:
    _create(supplier_service, "sup1", "Supplier A")
    products.save(
        ProductSheet(
            product=Product(id=ProductId("prod1"), name="Test Product", slug=Slug("test-product")),
            supply=ProductSupply(id=ProductId("prod1"), supplier_id=SupplierId("sup1")),
        ),
    )
    assert products.find_by_id(ProductId("prod1")) is not None

    supplier_service.delete_supplier("sup1").unwrap()

    assert products.find_by_id(ProductId("prod1")) is None


def test_should_get_suppliers_by_product(
    supplier_service: SupplierService, products: InMemoryProductRepository
) -> None:
    """Désactivé en Java (LAZY_LOADING_ISSUE.md) : le lien passe par la fiche du produit."""
    _create(supplier_service, "sup1", "Supplier A")
    _create(supplier_service, "sup2", "Supplier B")
    products.save(
        ProductSheet(
            product=Product(id=ProductId("prod1"), name="Test Product", slug=Slug("test-product")),
            supply=ProductSupply(id=ProductId("prod1"), supplier_id=SupplierId("sup1")),
        ),
    )

    suppliers = supplier_service.get_suppliers_by_product("prod1").unwrap()

    assert [s.id for s in suppliers] == [SupplierId("sup1")]


def test_should_raise_when_getting_suppliers_of_unknown_product(
    supplier_service: SupplierService,
) -> None:
    with pytest.raises(ValueError, match="Product not found"):
        supplier_service.get_suppliers_by_product("ghost")
