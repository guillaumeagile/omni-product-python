import pytest

from omni_product.domain.model import Product, ProductSupply
from omni_product.infrastructure.persistence.in_memory import (
    InMemoryRepository,
    InMemorySupplierRepository,
)


@pytest.fixture
def products() -> InMemoryRepository[Product]:
    return InMemoryRepository[Product]()


@pytest.fixture
def supplies() -> InMemoryRepository[ProductSupply]:
    return InMemoryRepository[ProductSupply]()


@pytest.fixture
def suppliers() -> InMemorySupplierRepository:
    return InMemorySupplierRepository()
