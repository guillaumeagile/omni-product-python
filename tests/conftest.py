from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from omni_product.config import Settings
from omni_product.infrastructure.persistence.in_memory import (
    InMemoryProductRepository,
    InMemorySupplierRepository,
)
from omni_product.main import create_app


@pytest.fixture
def app() -> Iterator[FastAPI]:
    """Une application neuve par test, avec ses données en mémoire."""
    application = create_app(Settings())
    with TestClient(application):  # déclenche le lifespan
        yield application


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def products(app: FastAPI) -> InMemoryProductRepository:
    return InMemoryProductRepository(app.state.products)


@pytest.fixture
def suppliers(app: FastAPI) -> InMemorySupplierRepository:
    return InMemorySupplierRepository(app.state.suppliers, app.state.products)
