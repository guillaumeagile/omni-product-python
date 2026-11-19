from datetime import date

from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from omni_product.dal import product_dal
from omni_product.domain.model.product import (
    NonExpiringProduct,
    PerishableProduct,
    Product,
    ProductId,
    ShelfLifeDays,
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


def test_kind_is_written_from_the_python_class(session: Session) -> None:
    product_dal.save(session, Product(id=ProductId("p1"), name="Stylo", slug=Slug("stylo")))
    product_dal.save(session, PerishableProduct(id=ProductId("p2"), name="Lait", slug=Slug("lait")))
    product_dal.save(session, NonExpiringProduct(id=ProductId("p3"), name="Sel", slug=Slug("sel")))

    kinds = dict(session.execute(text("SELECT id, kind FROM products ORDER BY id")).all())
    assert kinds == {"p1": "standard", "p2": "perishable", "p3": "non_expiring"}


def test_row_is_loaded_back_as_its_subclass(app: FastAPI) -> None:
    with app.state.session_factory() as writer:
        product_dal.save(
            writer,
            PerishableProduct(
                id=ProductId("p1"),
                name="Lait",
                slug=Slug("lait"),
                expiration_date=date(2026, 12, 1),
                shelf_life_days=ShelfLifeDays(7),
            ),
        )

    # Une session neuve : on recharge la ligne au lieu de réutiliser l'objet en mémoire.
    with app.state.session_factory() as reader:
        loaded = product_dal.find_by_id(reader, "p1")

        assert isinstance(loaded, PerishableProduct)
        assert loaded.expiration_date == date(2026, 12, 1)
        assert loaded.shelf_life_days == ShelfLifeDays(7)
        assert loaded.is_perishable()


def test_single_table_leaves_perishable_columns_null_for_other_kinds(session: Session) -> None:
    product_dal.save(session, NonExpiringProduct(id=ProductId("p1"), name="Sel", slug=Slug("sel")))

    expiration = session.execute(
        text("SELECT expiration_date FROM products WHERE id = 'p1'")
    ).scalar_one()
    assert expiration is None
