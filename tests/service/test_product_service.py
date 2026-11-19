from datetime import date
from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from omni_product.dal.product_dal import empty_rows
from omni_product.domain.model import freshness
from omni_product.domain.model.product import NonExpiringProduct, PerishableProduct
from omni_product.domain.model.product_values import (
    ExpirationDate,
    ProductId,
    ProductName,
    Slug,
)
from omni_product.service.product_service import ProductService


@pytest.fixture
def product_service(session: Session) -> ProductService:
    return ProductService(session)


def _perishable(id: str, name: str, slug: str, expires: date | None = None) -> PerishableProduct:
    return PerishableProduct(
        id=ProductId(id),
        name=ProductName(name),
        slug=Slug(slug),
        expiration_date=None if expires is None else ExpirationDate(expires),
    )


def test_find_expired_returns_only_perishable_products_past_their_date(
    product_service: ProductService,
) -> None:
    product_service.save(empty_rows(_perishable("p1", "Lait", "lait", date(2026, 11, 1))))
    product_service.save(empty_rows(_perishable("p2", "Yaourt", "yaourt", date(2026, 12, 1))))
    product_service.save(empty_rows(_perishable("p3", "Beurre", "beurre")))
    product_service.save(
        empty_rows(
            NonExpiringProduct(id=ProductId("p4"), name=ProductName("Sel"), slug=Slug("sel"))
        )
    )

    # Legacy : l'horloge se fige avec `patch`.
    # La règle 6 supprime ce besoin : l'heure passe en paramètre.
    with patch.object(freshness, "date") as fake_date:
        fake_date.today.return_value = date(2026, 11, 10)
        expired = product_service.find_expired()

    assert [product.id.value for product in expired] == ["p1"]
