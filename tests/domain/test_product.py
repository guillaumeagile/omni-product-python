"""Le modèle s'instancie sans session ni base : il ignore le stockage."""

from omni_product.domain.model import (
    NonExpiringProduct,
    PerishableProduct,
    Product,
    ProductPricing,
    ProductStorage,
    Supplier,
)


def test_is_perishable_is_true_only_for_perishable_products() -> None:
    assert PerishableProduct(id="p1", name="Lait", slug="lait").is_perishable()
    assert not NonExpiringProduct(id="p2", name="Sel", slug="sel").is_perishable()
    assert not Product(id="p3", name="Stylo", slug="stylo").is_perishable()


def test_perishable_fields_are_optional_in_memory() -> None:
    product = PerishableProduct(id="p1", name="Lait", slug="lait")

    assert product.expiration_date is None
    assert product.shelf_life_days is None


def test_contexts_are_plain_objects_without_session() -> None:
    assert ProductPricing(product_id="p1").discounts == []
    assert ProductStorage(product_id="p1", stock=3).stock == 3
    assert Supplier(id="s1", name="Acme").name == "Acme"
