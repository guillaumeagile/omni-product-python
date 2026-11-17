from omni_product.domain.model import (
    NonExpiring,
    Perishable,
    Product,
    ProductId,
    Slug,
)


def test_is_perishable_is_true_only_for_perishable_products() -> None:
    assert Product(
        id=ProductId("p1"), name="Lait", slug=Slug("lait"), shelf_life=Perishable()
    ).is_perishable()
    assert not Product(
        id=ProductId("p2"), name="Sel", slug=Slug("sel"), shelf_life=NonExpiring()
    ).is_perishable()
    assert not Product(id=ProductId("p3"), name="Stylo", slug=Slug("stylo")).is_perishable()


def test_perishable_fields_are_optional_in_memory() -> None:
    product = Product(id=ProductId("p1"), name="Lait", slug=Slug("lait"), shelf_life=Perishable())

    assert product.shelf_life == Perishable(expiration_date=None, shelf_life_days=None)
