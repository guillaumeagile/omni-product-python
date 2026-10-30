from fastapi.testclient import TestClient


def test_perishable_product_keeps_its_expiration_date(client: TestClient) -> None:
    yogurt = {
        "id": "p2",
        "name": "Yaourt",
        "slug": "yaourt",
        "kind": "perishable",
        "expirationDate": "2026-12-01",
        "shelfLifeDays": 14,
    }

    created = client.post("/api/products", json=yogurt)
    assert created.status_code == 200
    assert created.json()["kind"] == "perishable"

    fetched = client.get("/api/products/p2").json()
    assert fetched["expirationDate"] == "2026-12-01"
    assert fetched["shelfLifeDays"] == 14


def test_non_expiring_product_has_no_expiration_date(client: TestClient) -> None:
    salt = {"id": "p3", "name": "Sel", "slug": "sel", "kind": "non_expiring"}

    assert client.post("/api/products", json=salt).json()["kind"] == "non_expiring"

    fetched = client.get("/api/products/p3").json()
    assert fetched["kind"] == "non_expiring"
    assert fetched["expirationDate"] is None


def test_product_without_kind_is_standard(client: TestClient) -> None:
    created = client.post("/api/products", json={"id": "p4", "name": "Stylo", "slug": "stylo"})

    assert created.json()["kind"] == "standard"
