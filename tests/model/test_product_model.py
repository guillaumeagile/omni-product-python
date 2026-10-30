from datetime import date

from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from omni_product.model import NonExpiringProduct, PerishableProduct, Product


def test_is_perishable_is_true_only_for_perishable_products() -> None:
    assert PerishableProduct(id="p1", name="Lait", slug="lait").is_perishable()
    assert not NonExpiringProduct(id="p2", name="Sel", slug="sel").is_perishable()
    assert not Product(id="p3", name="Stylo", slug="stylo").is_perishable()


def test_perishable_fields_are_optional_in_memory() -> None:
    product = PerishableProduct(id="p1", name="Lait", slug="lait")

    assert product.expiration_date is None
    assert product.shelf_life_days is None


def test_kind_is_written_from_the_python_class(session: Session) -> None:
    session.add_all(
        [
            Product(id="p1", name="Stylo", slug="stylo"),
            PerishableProduct(id="p2", name="Lait", slug="lait"),
            NonExpiringProduct(id="p3", name="Sel", slug="sel"),
        ]
    )
    session.commit()

    kinds = dict(session.execute(text("SELECT id, kind FROM products ORDER BY id")).all())
    assert kinds == {"p1": "standard", "p2": "perishable", "p3": "non_expiring"}


def test_row_is_loaded_back_as_its_subclass(app: FastAPI) -> None:
    with app.state.session_factory() as writer:
        writer.add(
            PerishableProduct(
                id="p1",
                name="Lait",
                slug="lait",
                expiration_date=date(2026, 12, 1),
                shelf_life_days=7,
            )
        )
        writer.commit()

    # Une session neuve : on recharge la ligne au lieu de réutiliser l'objet en mémoire.
    with app.state.session_factory() as reader:
        loaded = reader.get(Product, "p1")

        assert isinstance(loaded, PerishableProduct)
        assert loaded.expiration_date == date(2026, 12, 1)
        assert loaded.shelf_life_days == 7
        assert loaded.is_perishable()


def test_single_table_leaves_perishable_columns_null_for_other_kinds(session: Session) -> None:
    session.add(NonExpiringProduct(id="p1", name="Sel", slug="sel"))
    session.commit()

    expiration = session.execute(
        text("SELECT expiration_date FROM products WHERE id = 'p1'")
    ).scalar_one()
    assert expiration is None
