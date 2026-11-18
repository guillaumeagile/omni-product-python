from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from omni_product.dal import product_dal, supplier_dal
from omni_product.dal.product_dal import ProductSheet
from omni_product.domain.model import (
    Product,
    ProductId,
    ProductSupply,
    Slug,
    Supplier,
    SupplierId,
)


def _supplier(supplier_id: str, name: str) -> Supplier:
    return Supplier(id=SupplierId(supplier_id), name=name)


def test_should_create_supplier(client: TestClient) -> None:
    response = client.post("/api/suppliers", json={"id": "sup1", "name": "Supplier A"})

    assert response.status_code == 201
    assert response.json() == {"id": "sup1", "name": "Supplier A"}


def test_should_refuse_supplier_without_name(client: TestClient) -> None:
    response = client.post("/api/suppliers", json={"id": "sup1"})

    assert response.status_code == 422


def test_should_get_supplier_by_id(client: TestClient, session: Session) -> None:
    supplier_dal.save(session, _supplier("sup1", "Supplier A"))

    response = client.get("/api/suppliers/sup1")

    assert response.status_code == 200
    assert response.json()["id"] == "sup1"
    assert response.json()["name"] == "Supplier A"


def test_should_return_not_found_for_non_existent_supplier(client: TestClient) -> None:
    assert client.get("/api/suppliers/nonexistent").status_code == 404


def test_should_get_all_suppliers(client: TestClient, session: Session) -> None:
    supplier_dal.save(session, _supplier("sup1", "Supplier A"))
    supplier_dal.save(session, _supplier("sup2", "Supplier B"))

    response = client.get("/api/suppliers")

    assert response.status_code == 200
    assert [s["name"] for s in response.json()] == ["Supplier A", "Supplier B"]


def test_should_get_suppliers_by_product(client: TestClient, session: Session) -> None:
    supplier_dal.save(session, _supplier("sup1", "Supplier A"))
    supplier_dal.save(session, _supplier("sup2", "Supplier B"))
    product_dal.save(
        session,
        ProductSheet(
            product=Product(id=ProductId("prod1"), name="Test Product", slug=Slug("test-product")),
            supply=ProductSupply(id=ProductId("prod1"), supplier_id=SupplierId("sup1")),
        ),
    )

    response = client.get("/api/suppliers/product/prod1")

    assert response.status_code == 200
    assert [s["id"] for s in response.json()] == ["sup1"]


def test_should_update_supplier(client: TestClient, session: Session) -> None:
    supplier_dal.save(session, _supplier("sup1", "Supplier A"))

    response = client.put("/api/suppliers/sup1", json={"name": "Updated Supplier A"})

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Supplier A"


def test_should_delete_supplier(client: TestClient, session: Session) -> None:
    supplier_dal.save(session, _supplier("sup1", "Supplier A"))

    assert client.delete("/api/suppliers/sup1").status_code == 204
    assert client.get("/api/suppliers/sup1").status_code == 404


def test_should_cascade_delete_products_when_supplier_deleted(
    client: TestClient, session: Session
) -> None:
    supplier_dal.save(session, _supplier("sup1", "Supplier A"))
    product_dal.save(
        session,
        ProductSheet(
            product=Product(id=ProductId("prod1"), name="Test Product", slug=Slug("test-product")),
            supply=ProductSupply(id=ProductId("prod1"), supplier_id=SupplierId("sup1")),
        ),
    )

    assert client.delete("/api/suppliers/sup1").status_code == 204

    assert client.get("/api/products/prod1").status_code == 404
