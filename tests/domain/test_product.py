"""Le modèle s'instancie sans session ni base : il ignore le stockage."""

from omni_product.domain.model import (
    NonExpiringProduct,
    PerishableProduct,
    Product,
    ProductId,
    ProductPricing,
    ProductStorage,
    Quantity,
    Slug,
    Supplier,
    SupplierId,
)


def test_is_perishable_is_true_only_for_perishable_products() -> None:
    assert PerishableProduct(id=ProductId("p1"), name="Lait", slug=Slug("lait")).is_perishable()
    assert not NonExpiringProduct(id=ProductId("p2"), name="Sel", slug=Slug("sel")).is_perishable()
    assert not Product(id=ProductId("p3"), name="Stylo", slug=Slug("stylo")).is_perishable()


def test_perishable_fields_are_optional_in_memory() -> None:
    product = PerishableProduct(id=ProductId("p1"), name="Lait", slug=Slug("lait"))

    assert product.expiration_date is None
    assert product.shelf_life_days is None


def test_contexts_are_plain_objects_without_session() -> None:
    assert ProductPricing(id=ProductId("p1")).discounts == []
    assert ProductStorage(id=ProductId("p1"), stock=Quantity(3)).stock == Quantity(3)
    assert Supplier(id=SupplierId("s1"), name="Acme").name == "Acme"


def test_contexts_share_the_identity_of_the_product() -> None:
    product = Product(id=ProductId("p1"), name="Stylo", slug=Slug("stylo"))

    assert ProductPricing(id=product.id).id == ProductId("p1")
