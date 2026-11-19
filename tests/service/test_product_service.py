from datetime import date
from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from omni_product.domain.model import (
    NonExpiringProduct,
    PerishableProduct,
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
    product_service.save(
        PerishableProduct(
            id=ProductId("p1"), name="Lait", slug=Slug("lait"), expiration_date=date(2026, 11, 1)
        )
    )
    product_service.save(
        PerishableProduct(
            id=ProductId("p2"),
            name="Yaourt",
            slug=Slug("yaourt"),
            expiration_date=date(2026, 12, 1),
        )
    )
    product_service.save(PerishableProduct(id=ProductId("p3"), name="Beurre", slug=Slug("beurre")))
    product_service.save(NonExpiringProduct(id=ProductId("p4"), name="Sel", slug=Slug("sel")))

    # Legacy : l'horloge se fige avec `patch`.
    # La règle 6 supprime ce besoin : l'heure passe en paramètre.
    with patch.object(freshness, "date") as fake_date:
        fake_date.today.return_value = date(2026, 11, 10)
        expired = product_service.find_expired()

    assert [product.id for product in expired] == [ProductId("p1")]
