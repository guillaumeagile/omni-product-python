from fastapi.testclient import TestClient


def test_a_negative_quantity_is_refused_with_422(client: TestClient) -> None:
    response = client.post(
        "/api/products",
        json={"id": "p9", "name": "Sel", "slug": "sel", "quantity": -1},
    )
    assert response.status_code == 422
    assert "négatif" in response.json()["detail"]


def test_a_blank_slug_is_refused_with_422(client: TestClient) -> None:
    response = client.post("/api/products", json={"id": "p9", "name": "Sel", "slug": " "})
    assert response.status_code == 422
    assert client.get("/api/products/p9").status_code == 404
