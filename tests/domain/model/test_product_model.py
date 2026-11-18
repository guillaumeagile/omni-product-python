from datetime import date

from omni_product.domain.model import (
    NonExpiring,
    ParDateLimite,
    ParDureeDeConservation,
    Product,
    ProductId,
    ShelfLifeDays,
    Slug,
)


def test_is_perishable_is_true_only_for_perishable_products() -> None:
    assert Product(
        id=ProductId("p1"),
        name="Lait",
        slug=Slug("lait"),
        shelf_life=ParDateLimite(date(2026, 12, 1)),
    ).is_perishable()
    assert Product(
        id=ProductId("p2"),
        name="Yaourt",
        slug=Slug("yaourt"),
        shelf_life=ParDureeDeConservation(ShelfLifeDays(7)),
    ).is_perishable()
    assert not Product(
        id=ProductId("p3"), name="Sel", slug=Slug("sel"), shelf_life=NonExpiring()
    ).is_perishable()
    assert not Product(id=ProductId("p4"), name="Stylo", slug=Slug("stylo")).is_perishable()
