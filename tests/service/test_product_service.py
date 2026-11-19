from datetime import date
from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from omni_product.domain.model import (
    NonExpiring,
    Perishable,
    Product,
    ProductId,
    Slug,
    freshness,
)
from omni_product.service.product_service import ProductService


@pytest.fixture
def product_service(session: Session) -> ProductService:
    return ProductService(session)


def test_find_expired_returns_only_perishable_products_past_their_date(
    product_service: ProductService,
) -> None:
    def product(product_id: str, shelf_life: Perishable | NonExpiring | None) -> Product:
        return Product(
            id=ProductId(product_id), name=product_id, slug=Slug(product_id), shelf_life=shelf_life
        )

    product_service.save(product("lait", Perishable(expiration_date=date(2026, 11, 1))))
    product_service.save(product("yaourt", Perishable(expiration_date=date(2026, 12, 1))))
    product_service.save(product("beurre", Perishable()))
    product_service.save(product("sel", NonExpiring()))
    product_service.save(product("stylo", None))

    # Legacy : l'horloge se fige avec `patch`.
    # La règle 6 supprime ce besoin : l'heure passe en paramètre.
    with patch.object(freshness, "date") as fake_date:
        fake_date.today.return_value = date(2026, 11, 10)
        expired = product_service.find_expired()

    assert [expired_product.id for expired_product in expired] == [ProductId("lait")]
