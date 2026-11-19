from datetime import date
from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from omni_product.anemic_model import (
    NonExpiringProduct,
    PerishableProduct,
    Price,
    ProductPrice,
    ProductShipment,
    ProductStock,
    RegionSupplier,
    Warehouse,
)
from omni_product.domain.model import freshness
from omni_product.service.product_service import ProductService


@pytest.fixture
def product_service(session: Session) -> ProductService:
    return ProductService(session)


def test_should_delete_stock_and_shipment_with_their_product(
    product_service: ProductService,
) -> None:
    product_service.save(NonExpiringProduct(id="p1", name="Sel", slug="sel"))
    product_service.save_stock(
        ProductStock(product_id="p1", quantity=3, stock=2, warehouse=Warehouse(location="Nord"))
    )
    product_service.save_shipment(ProductShipment(product_id="p1", kilos=1.5, volume="10x10"))

    product_service.delete_by_id("p1")

    assert product_service.find_stock("p1") is None
    assert product_service.find_shipment("p1") is None


def test_should_replace_suppliers_regions_on_each_save(product_service: ProductService) -> None:
    product_service.save(NonExpiringProduct(id="p1", name="Sel", slug="sel"))
    product_service.replace_suppliers_regions("p1", {"Nord": RegionSupplier(name="A")})

    product_service.replace_suppliers_regions("p1", {"Nord": RegionSupplier(name="B")})

    assert product_service.find_suppliers_regions("p1") == {"Nord": RegionSupplier(name="B")}


def test_should_delete_price_and_discounts_with_their_product(
    product_service: ProductService,
) -> None:
    product_service.save(NonExpiringProduct(id="p1", name="Sel", slug="sel"))
    product_service.save_price(ProductPrice(product_id="p1", price=Price(base=10.0, tax=2.0)))
    product_service.replace_discounts("p1", ["Soldes", "Fidélité"])

    product_service.delete_by_id("p1")

    assert product_service.find_price("p1") is None
    assert product_service.find_discounts("p1") == []


def test_find_expired_returns_only_perishable_products_past_their_date(
    product_service: ProductService,
) -> None:
    product_service.save(
        PerishableProduct(id="p1", name="Lait", slug="lait", expiration_date=date(2026, 11, 1))
    )
    product_service.save(
        PerishableProduct(id="p2", name="Yaourt", slug="yaourt", expiration_date=date(2026, 12, 1))
    )
    product_service.save(PerishableProduct(id="p3", name="Beurre", slug="beurre"))
    product_service.save(NonExpiringProduct(id="p4", name="Sel", slug="sel"))

    # Legacy : l'horloge se fige avec `patch`.
    # La règle 6 supprime ce besoin : l'heure passe en paramètre.
    with patch.object(freshness, "date") as fake_date:
        fake_date.today.return_value = date(2026, 11, 10)
        expired = product_service.find_expired()

    assert [product.id for product in expired] == ["p1"]
