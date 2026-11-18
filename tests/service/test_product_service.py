from datetime import date

import pytest

from omni_product.domain.model import (
    NonExpiring,
    ParDateLimite,
    ParDureeDeConservation,
    Perishable,
    Product,
    ProductId,
    ShelfLifeDays,
    Slug,
)
from omni_product.infrastructure.persistence.in_memory import InMemoryRepository
from omni_product.service.product_service import ProductService


class FakeClock:
    def __init__(self, today: date) -> None:
        self._today = today

    def today(self) -> date:
        return self._today


@pytest.fixture
def product_service(products: InMemoryRepository[Product]) -> ProductService:
    return ProductService(products)


def _product(product_id: str, shelf_life: Perishable | NonExpiring | None) -> Product:
    return Product(
        id=ProductId(product_id), name=product_id, slug=Slug(product_id), shelf_life=shelf_life
    )


def test_find_expired_returns_only_perishable_products_past_their_date(
    product_service: ProductService,
) -> None:
    product_service.save(_product("p1", ParDateLimite(date(2026, 11, 1))))
    product_service.save(_product("p2", ParDateLimite(date(2026, 12, 1))))
    product_service.save(_product("p3", ParDureeDeConservation(ShelfLifeDays(3))))
    product_service.save(_product("p4", NonExpiring()))

    expired = product_service.find_expired(FakeClock(date(2026, 11, 10)))

    assert [product.id.value for product in expired] == ["p1"]
