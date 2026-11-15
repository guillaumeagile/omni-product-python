from omni_product.domain.model import (
    NonExpiringProduct,
    PerishableProduct,
    Product,
    ProductId,
    Slug,
)


def test_is_perishable_is_true_only_for_perishable_products() -> None:
    assert PerishableProduct(id=ProductId("p1"), name="Lait", slug=Slug("lait")).is_perishable()
    assert not NonExpiringProduct(id=ProductId("p2"), name="Sel", slug=Slug("sel")).is_perishable()
    assert not Product(id=ProductId("p3"), name="Stylo", slug=Slug("stylo")).is_perishable()


def test_perishable_fields_are_optional_in_memory() -> None:
    product = PerishableProduct(id=ProductId("p1"), name="Lait", slug=Slug("lait"))

    assert product.expiration_date is None
    assert product.shelf_life_days is None
