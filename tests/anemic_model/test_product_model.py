from datetime import date

from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from omni_product.dal import product_dal
from omni_product.domain.model.product import (
    NonExpiring,
    Perishable,
    Product,
    ProductId,
    ShelfLifeDays,
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


def test_kind_is_written_from_the_shelf_life(session: Session) -> None:
    product_dal.save(session, Product(id=ProductId("p1"), name="Stylo", slug=Slug("stylo")))
    product_dal.save(
        session,
        Product(id=ProductId("p2"), name="Lait", slug=Slug("lait"), shelf_life=Perishable()),
    )
    product_dal.save(
        session,
        Product(id=ProductId("p3"), name="Sel", slug=Slug("sel"), shelf_life=NonExpiring()),
    )

    kinds = dict(session.execute(text("SELECT id, kind FROM products ORDER BY id")).all())
    assert kinds == {"p1": "standard", "p2": "perishable", "p3": "non_expiring"}


def test_row_is_loaded_back_with_its_shelf_life(app: FastAPI) -> None:
    with app.state.session_factory() as writer:
        product_dal.save(
            writer,
            Product(
                id=ProductId("p1"),
                name="Lait",
                slug=Slug("lait"),
                shelf_life=Perishable(
                    expiration_date=date(2026, 12, 1), shelf_life_days=ShelfLifeDays(7)
                ),
            ),
        )

    # Une session neuve : on recharge la ligne au lieu de réutiliser l'objet en mémoire.
    with app.state.session_factory() as reader:
        loaded = product_dal.find_by_id(reader, ProductId("p1"))

        assert loaded is not None
        assert loaded.shelf_life == Perishable(
            expiration_date=date(2026, 12, 1), shelf_life_days=ShelfLifeDays(7)
        )
        assert loaded.is_perishable()


def test_single_table_leaves_perishable_columns_null_for_other_kinds(session: Session) -> None:
    product_dal.save(
        session,
        Product(id=ProductId("p1"), name="Sel", slug=Slug("sel"), shelf_life=NonExpiring()),
    )

    expiration = session.execute(
        text("SELECT expiration_date FROM products WHERE id = 'p1'")
    ).scalar_one()
    assert expiration is None
