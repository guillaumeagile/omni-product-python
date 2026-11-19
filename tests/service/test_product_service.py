from datetime import date
from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from omni_product.domain.model import freshness
from omni_product.domain.model.pricing import BasePrice, Price, ProductPrice, TaxAmount
from omni_product.domain.model.product import (
    NonExpiringProduct,
    PerishableProduct,
    ProductId,
    Slug,
)
from omni_product.domain.model.shipment import Kilos, ProductShipment, Volume
from omni_product.domain.model.stock import (
    ProductStock,
    Quantity,
    Stock,
    Warehouse,
    WarehouseLocation,
)
from omni_product.domain.model.supplier_region import RegionSupplier
from omni_product.service.product_service import ProductService


@pytest.fixture
def product_service(session: Session) -> ProductService:
    return ProductService(session)


def test_should_delete_stock_and_shipment_with_their_product(
    product_service: ProductService,
) -> None:
    product_service.save(NonExpiringProduct(id=ProductId("p1"), name="Sel", slug=Slug("sel")))
    product_service.save_stock(
        ProductStock(
            id=ProductId("p1"),
            quantity=Quantity(3),
            stock=Stock(2),
            warehouse=Warehouse(location=WarehouseLocation("Nord")),
        )
    )
    product_service.save_shipment(
        ProductShipment(id=ProductId("p1"), kilos=Kilos(1.5), volume=Volume("10x10"))
    )

    product_service.delete_by_id("p1")

    assert product_service.find_stock("p1") is None
    assert product_service.find_shipment("p1") is None


def test_should_replace_suppliers_regions_on_each_save(product_service: ProductService) -> None:
    product_service.save(NonExpiringProduct(id=ProductId("p1"), name="Sel", slug=Slug("sel")))
    product_service.replace_suppliers_regions("p1", {"Nord": RegionSupplier(name="A")})

    product_service.replace_suppliers_regions("p1", {"Nord": RegionSupplier(name="B")})

    assert product_service.find_suppliers_regions("p1") == {"Nord": RegionSupplier(name="B")}


def test_should_delete_price_and_discounts_with_their_product(
    product_service: ProductService,
) -> None:
    product_service.save(NonExpiringProduct(id=ProductId("p1"), name="Sel", slug=Slug("sel")))
    product_service.save_price(
        ProductPrice(id=ProductId("p1"), price=Price(base=BasePrice(10.0), tax=TaxAmount(2.0)))
    )
    product_service.replace_discounts("p1", ["Soldes", "Fidélité"])

    product_service.delete_by_id("p1")

    assert product_service.find_price("p1") is None
    assert product_service.find_discounts("p1") == []


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
