from fastapi.testclient import TestClient


def test_crud_operations(client: TestClient) -> None:
    product = {
        "id": "p1",
        "name": "Test Product",
        "slug": "test-product",
        "price": {"base": 100.0, "tax": 20.0, "taxRate": 0.2},
        "discounts": ["Image 1"],
        "images": {"main": "image-url"},
        "suppliersRegions": {
            "Europe": {"name": "Supplier1", "siren": "SIREN123", "tvaId": "TVA456"}
        },
        "kilos": 23.0,
        "volume": "10x10x10",
        "quantity": 100,
        "stock": 50,
        "warehouse": {"location": "Main Warehouse"},
    }

    # Create
    created = client.post("/api/products", json=product)
    assert created.status_code == 200
    body = created.json()
    assert body["id"] == "p1"
    assert body["name"] == "Test Product"
    assert body["images"]["main"] == "image-url"
    assert body["suppliersRegions"]["Europe"] == {
        "name": "Supplier1",
        "siren": "SIREN123",
        "tvaId": "TVA456",
    }
    assert body["price"] == {"base": 100.0, "tax": 20.0, "taxRate": 0.2}
    assert body["warehouse"] == {"location": "Main Warehouse"}

    # Validation rule: the name is required
    assert client.post("/api/products", json={"name": "", "slug": "vide"}).status_code == 424

    # Get all
    all_products = client.get("/api/products")
    assert all_products.status_code == 200
    assert all_products.json()[0]["id"] == "p1"

    # Get by id
    fetched = client.get("/api/products/p1")
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "Test Product"

    # Update (collections are replaced, not merged)
    updated_payload = {
        **product,
        "name": "Updated Product",
        "slug": "updated-product",
        "discounts": ["D1"],
        "suppliersRegions": {"Asia": {"name": "Supplier2", "siren": "SIREN789", "tvaId": "TVA012"}},
    }
    updated = client.put("/api/products/p1", json=updated_payload)
    assert updated.status_code == 200
    assert updated.json()["name"] == "Updated Product"
    assert updated.json()["discounts"] == ["D1"]
    assert list(updated.json()["suppliersRegions"]) == ["Asia"]

    # Delete
    assert client.delete("/api/products/p1").status_code == 204

    # Get by id (not found)
    assert client.get("/api/products/p1").status_code == 404


def test_update_and_delete_unknown_product_return_not_found(client: TestClient) -> None:
    assert client.put("/api/products/ghost", json={"name": "x", "slug": "x"}).status_code == 404
    assert client.delete("/api/products/ghost").status_code == 404


def test_create_product_without_id_is_rejected(client: TestClient) -> None:
    assert client.post("/api/products", json={"name": "No id", "slug": "no-id"}).status_code == 422


def test_create_or_update_product_without_name_or_slug_is_rejected(client: TestClient) -> None:
    assert client.post("/api/products", json={"id": "p1", "slug": "s"}).status_code == 422
    assert client.post("/api/products", json={"id": "p1", "name": "n"}).status_code == 422
    client.post("/api/products", json={"id": "p1", "name": "Stylo", "slug": "stylo"})
    assert client.put("/api/products/p1", json={"slug": "stylo"}).status_code == 422


def test_update_product_with_blank_name_is_rejected(client: TestClient) -> None:
    client.post("/api/products", json={"id": "p1", "name": "Stylo", "slug": "stylo"})

    assert client.put("/api/products/p1", json={"name": "  ", "slug": "stylo"}).status_code == 424
