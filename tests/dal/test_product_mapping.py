"""Le branchement du modèle sur la base : `dal/mapping.py`."""

from datetime import date

from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from omni_product.domain.model import (
    NonExpiringProduct,
    PerishableProduct,
    Product,
    ProductId,
    ShelfLifeDays,
    Slug,
)


def test_kind_is_written_from_the_python_class(session: Session) -> None:
    session.add_all(
        [
            Product(id=ProductId("p1"), name="Stylo", slug=Slug("stylo")),
            PerishableProduct(id=ProductId("p2"), name="Lait", slug=Slug("lait")),
            NonExpiringProduct(id=ProductId("p3"), name="Sel", slug=Slug("sel")),
        ]
    )
    session.commit()

    kinds = dict(session.execute(text("SELECT id, kind FROM products ORDER BY id")).all())
    assert kinds == {"p1": "standard", "p2": "perishable", "p3": "non_expiring"}


def test_row_is_loaded_back_as_its_subclass(app: FastAPI) -> None:
    with app.state.session_factory() as writer:
        writer.add(
            PerishableProduct(
                id=ProductId("p1"),
                name="Lait",
                slug=Slug("lait"),
                expiration_date=date(2026, 12, 1),
                shelf_life_days=ShelfLifeDays(7),
            )
        )
        writer.commit()

    # Une session neuve : on recharge la ligne au lieu de réutiliser l'objet en mémoire.
    with app.state.session_factory() as reader:
        loaded = reader.get(Product, ProductId("p1"))

        assert isinstance(loaded, PerishableProduct)
        assert loaded.expiration_date == date(2026, 12, 1)
        assert loaded.shelf_life_days == ShelfLifeDays(7)
        assert loaded.is_perishable()


def test_single_table_leaves_perishable_columns_null_for_other_kinds(session: Session) -> None:
    session.add(NonExpiringProduct(id=ProductId("p1"), name="Sel", slug=Slug("sel")))
    session.commit()

    expiration = session.execute(
        text("SELECT expiration_date FROM products WHERE id = 'p1'")
    ).scalar_one()
    assert expiration is None
