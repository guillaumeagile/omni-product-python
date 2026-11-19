"""Le modèle s'instancie sans session ni base : il ignore le stockage."""

from omni_product.domain.model import (
    NonExpiring,
    Perishable,
    Product,
    ProductId,
    ProductPricing,
    ProductStorage,
    Quantity,
    Slug,
    Supplier,
    SupplierId,
)


def _product(shelf_life: Perishable | NonExpiring | None = None) -> Product:
    return Product(id=ProductId("p1"), name="Lait", slug=Slug("lait"), shelf_life=shelf_life)


def test_is_perishable_is_true_only_for_perishable_products() -> None:
    assert _product(Perishable()).is_perishable() is True
    assert _product(NonExpiring()).is_perishable() is False
    assert _product().is_perishable() is False


def test_a_product_without_shelf_life_is_standard() -> None:
    assert Product(id=ProductId("p1"), name="Stylo", slug=Slug("stylo")).shelf_life is None


def test_perishable_fields_are_optional_in_memory() -> None:
    assert Perishable() == Perishable(expiration_date=None, shelf_life_days=None)


def test_contexts_are_plain_objects_without_session() -> None:
    assert ProductPricing(id=ProductId("p1")).discounts == []
    assert ProductStorage(id=ProductId("p1"), stock=Quantity(3)).stock == Quantity(3)
    assert Supplier(id=SupplierId("s1"), name="Acme").name == "Acme"


def test_contexts_share_the_identity_of_the_product() -> None:
    product = Product(id=ProductId("p1"), name="Stylo", slug=Slug("stylo"))

    assert ProductPricing(id=product.id).id == ProductId("p1")
