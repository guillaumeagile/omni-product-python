from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from omni_product.model import Product, Supplier
from omni_product.repository.product_repository import ProductRepository
from omni_product.repository.supplier_repository import SupplierRepository


def _supplier(
    supplier_id: str, name: str, country: str = "France", region: str = "Île-de-France"
) -> Supplier:
    return Supplier(
        id=supplier_id,
        name=name,
        contact_email=f"contact@{name.replace(' ', '').lower()}.com",
        contact_phone="+33123456789",
        country=country,
        region=region,
    )


def test_should_create_supplier(client: TestClient) -> None:
    response = client.post(
        "/api/suppliers",
        json={
            "id": "sup1",
            "name": "Supplier A",
            "contactEmail": "contact@suppliera.com",
            "contactPhone": "+33123456789",
            "country": "France",
            "region": "Île-de-France",
        },
    )

    assert response.status_code == 201
    assert response.json()["id"] == "sup1"
    assert response.json()["name"] == "Supplier A"
    assert response.json()["country"] == "France"
    assert response.json()["contactEmail"] == "contact@suppliera.com"


def test_should_get_supplier_by_id(
    client: TestClient, supplier_repository: SupplierRepository
) -> None:
    supplier_repository.save(_supplier("sup1", "Supplier A"))

    response = client.get("/api/suppliers/sup1")

    assert response.status_code == 200
    assert response.json()["id"] == "sup1"
    assert response.json()["name"] == "Supplier A"


def test_should_return_not_found_for_non_existent_supplier(client: TestClient) -> None:
    assert client.get("/api/suppliers/nonexistent").status_code == 404


def test_should_get_all_suppliers(
    client: TestClient, supplier_repository: SupplierRepository
) -> None:
    supplier_repository.save(_supplier("sup1", "Supplier A"))
    supplier_repository.save(_supplier("sup2", "Supplier B", "Spain", "Madrid"))

    response = client.get("/api/suppliers")

    assert response.status_code == 200
    assert [s["name"] for s in response.json()] == ["Supplier A", "Supplier B"]


def test_should_get_suppliers_by_country(
    client: TestClient, supplier_repository: SupplierRepository
) -> None:
    supplier_repository.save(_supplier("sup1", "Supplier A"))
    supplier_repository.save(_supplier("sup2", "Supplier B", "Spain", "Madrid"))

    response = client.get("/api/suppliers/country/France")

    assert response.status_code == 200
    assert [s["name"] for s in response.json()] == ["Supplier A"]


def test_should_get_suppliers_by_region(
    client: TestClient, supplier_repository: SupplierRepository
) -> None:
    supplier_repository.save(_supplier("sup1", "Supplier A"))
    supplier_repository.save(_supplier("sup2", "Supplier B", region="Provence"))

    response = client.get("/api/suppliers/region/Île-de-France")

    assert response.status_code == 200
    assert [s["name"] for s in response.json()] == ["Supplier A"]


def test_should_get_suppliers_by_product(
    client: TestClient,
    supplier_repository: SupplierRepository,
    product_repository: ProductRepository,
) -> None:
    supplier_repository.save(_supplier("sup1", "Supplier A"))
    supplier_repository.save(_supplier("sup2", "Supplier B"))
    product_repository.save(
        Product(id="prod1", name="Test Product", slug="test-product", supplier_id="sup1")
    )

    response = client.get("/api/suppliers/product/prod1")

    assert response.status_code == 200
    assert [s["id"] for s in response.json()] == ["sup1"]


def test_should_update_supplier(
    client: TestClient, supplier_repository: SupplierRepository
) -> None:
    supplier_repository.save(_supplier("sup1", "Supplier A"))

    response = client.put(
        "/api/suppliers/sup1",
        json={
            "name": "Updated Supplier A",
            "contactEmail": "newemail@suppliera.com",
            "contactPhone": "+33111111111",
            "country": "Germany",
            "region": "Berlin",
        },
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Supplier A"
    assert response.json()["country"] == "Germany"


def test_should_delete_supplier(
    client: TestClient, supplier_repository: SupplierRepository
) -> None:
    supplier_repository.save(_supplier("sup1", "Supplier A"))

    assert client.delete("/api/suppliers/sup1").status_code == 204
    assert client.get("/api/suppliers/sup1").status_code == 404


def test_should_cascade_delete_products_when_supplier_deleted(
    client: TestClient,
    supplier_repository: SupplierRepository,
    product_repository: ProductRepository,
    session: Session,
) -> None:
    supplier_repository.save(_supplier("sup1", "Supplier A"))
    product_repository.save(
        Product(id="prod1", name="Test Product", slug="test-product", supplier_id="sup1")
    )

    assert client.delete("/api/suppliers/sup1").status_code == 204

    assert client.get("/api/products/prod1").status_code == 404
