import pytest
from sqlalchemy.orm import Session

from omni_product.dal import product_dal
from omni_product.domain.model.product import Product, ProductId, Slug
from omni_product.domain.model.supplier import Country, Email, Phone, Region, SupplierId
from omni_product.service.supplier_service import SupplierService


@pytest.fixture
def supplier_service(session: Session) -> SupplierService:
    return SupplierService(session)


def _create(
    service: SupplierService,
    supplier_id: str,
    name: str,
    country: str = "France",
    region: str = "Île-de-France",
) -> None:
    service.create_supplier(
        SupplierId(supplier_id),
        name,
        Email("contact@test.com"),
        Phone("+33123456789"),
        Country(country),
        Region(region),
    )


def test_should_create_supplier(supplier_service: SupplierService) -> None:
    supplier = supplier_service.create_supplier(
        SupplierId("sup1"),
        "Supplier A",
        Email("contact@suppliera.com"),
        Phone("+33123456789"),
        Country("France"),
        Region("Île-de-France"),
    )

    assert supplier.id == SupplierId("sup1")
    assert supplier.name == "Supplier A"
    assert supplier.country == Country("France")


def test_should_get_supplier_by_id(supplier_service: SupplierService) -> None:
    _create(supplier_service, "sup1", "Supplier A")

    found = supplier_service.get_supplier(SupplierId("sup1"))

    assert found is not None
    assert found.id == SupplierId("sup1")
    assert found.name == "Supplier A"


def test_should_return_none_for_non_existent_supplier(supplier_service: SupplierService) -> None:
    assert supplier_service.get_supplier(SupplierId("nonexistent")) is None


def test_should_get_all_suppliers(supplier_service: SupplierService) -> None:
    _create(supplier_service, "sup1", "Supplier A")
    _create(supplier_service, "sup2", "Supplier B", "Spain", "Madrid")

    names = [s.name for s in supplier_service.get_all_suppliers()]

    assert names == ["Supplier A", "Supplier B"]


def test_should_get_suppliers_by_country(supplier_service: SupplierService) -> None:
    _create(supplier_service, "sup1", "Supplier A")
    _create(supplier_service, "sup2", "Supplier B", "Spain", "Madrid")

    french = supplier_service.get_suppliers_by_country(Country("France"))

    assert [s.name for s in french] == ["Supplier A"]


def test_should_get_suppliers_by_region(supplier_service: SupplierService) -> None:
    _create(supplier_service, "sup1", "Supplier A")
    _create(supplier_service, "sup2", "Supplier B", region="Provence")

    idf = supplier_service.get_suppliers_by_region(Region("Île-de-France"))

    assert [s.name for s in idf] == ["Supplier A"]


def test_should_update_supplier(supplier_service: SupplierService) -> None:
    _create(supplier_service, "sup1", "Supplier A")

    updated = supplier_service.update_supplier(
        SupplierId("sup1"),
        "Updated Supplier A",
        Email("newemail@suppliera.com"),
        Phone("+33111111111"),
        Country("Germany"),
        Region("Berlin"),
    )

    assert updated.name == "Updated Supplier A"
    assert updated.country == Country("Germany")
    assert updated.region == Region("Berlin")


def test_should_raise_when_updating_non_existent_supplier(
    supplier_service: SupplierService,
) -> None:
    with pytest.raises(ValueError, match="Supplier not found"):
        supplier_service.update_supplier(
            SupplierId("nonexistent"),
            "Name",
            Email("e@test.com"),
            Phone("+33"),
            Country("France"),
            Region("IDF"),
        )


def test_should_delete_supplier(supplier_service: SupplierService) -> None:
    _create(supplier_service, "sup1", "Supplier A")

    supplier_service.delete_supplier(SupplierId("sup1"))

    assert supplier_service.get_supplier(SupplierId("sup1")) is None


def test_should_raise_when_deleting_non_existent_supplier(
    supplier_service: SupplierService,
) -> None:
    with pytest.raises(ValueError, match="Supplier not found"):
        supplier_service.delete_supplier(SupplierId("nonexistent"))


def test_should_cascade_delete_products_when_supplier_deleted(
    supplier_service: SupplierService, session: Session
) -> None:
    _create(supplier_service, "sup1", "Supplier A")
    product_dal.save(
        session,
        Product(
            id=ProductId("prod1"),
            name="Test Product",
            slug=Slug("test-product"),
            supplier_id=SupplierId("sup1"),
        ),
    )
    assert product_dal.find_by_id(session, ProductId("prod1")) is not None

    supplier_service.delete_supplier(SupplierId("sup1"))

    assert product_dal.find_by_id(session, ProductId("prod1")) is None


def test_should_get_suppliers_by_product(
    supplier_service: SupplierService, session: Session
) -> None:
    """Désactivé en Java (LAZY_LOADING_ISSUE.md) : une requête SQL évite le lazy loading."""
    _create(supplier_service, "sup1", "Supplier A")
    _create(supplier_service, "sup2", "Supplier B")
    product_dal.save(
        session,
        Product(
            id=ProductId("prod1"),
            name="Test Product",
            slug=Slug("test-product"),
            supplier_id=SupplierId("sup1"),
        ),
    )

    suppliers = supplier_service.get_suppliers_by_product(ProductId("prod1"))

    assert [s.id for s in suppliers] == [SupplierId("sup1")]


def test_should_raise_when_getting_suppliers_of_unknown_product(
    supplier_service: SupplierService,
) -> None:
    with pytest.raises(ValueError, match="Product not found"):
        supplier_service.get_suppliers_by_product(ProductId("ghost"))
