"""Le branchement du modèle sur la base : `dal/mapping.py`."""

from datetime import date

from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from omni_product.domain.model import (
    NonExpiring,
    Perishable,
    Product,
    ProductId,
    ShelfLifeDays,
    Slug,
)


def test_kind_is_written_from_the_shelf_life(session: Session) -> None:
    session.add_all(
        [
            Product(id=ProductId("p1"), name="Stylo", slug=Slug("stylo")),
            Product(id=ProductId("p2"), name="Lait", slug=Slug("lait"), shelf_life=Perishable()),
            Product(id=ProductId("p3"), name="Sel", slug=Slug("sel"), shelf_life=NonExpiring()),
        ]
    )
    session.commit()

    kinds = dict(session.execute(text("SELECT id, kind FROM products ORDER BY id")).all())
    assert kinds == {"p1": "standard", "p2": "perishable", "p3": "non_expiring"}


def test_row_is_loaded_back_with_its_shelf_life(app: FastAPI) -> None:
    shelf_life = Perishable(expiration_date=date(2026, 12, 1), shelf_life_days=ShelfLifeDays(7))
    with app.state.session_factory() as writer:
        writer.add(
            Product(id=ProductId("p1"), name="Lait", slug=Slug("lait"), shelf_life=shelf_life)
        )
        writer.commit()

    # Une session neuve : on recharge la ligne au lieu de réutiliser l'objet en mémoire.
    with app.state.session_factory() as reader:
        loaded = reader.get(Product, ProductId("p1"))

        assert loaded is not None
        assert loaded.shelf_life == shelf_life
        assert loaded.is_perishable()


def test_shelf_life_change_is_saved_on_an_existing_product(app: FastAPI) -> None:
    with app.state.session_factory() as writer:
        product = Product(id=ProductId("p1"), name="Lait", slug=Slug("lait"))
        writer.add(product)
        writer.commit()
        product.shelf_life = NonExpiring()
        writer.commit()

    with app.state.session_factory() as reader:
        loaded = reader.get(Product, ProductId("p1"))

        assert loaded is not None
        assert loaded.shelf_life == NonExpiring()


def test_perishable_columns_stay_null_for_other_kinds(session: Session) -> None:
    session.add(Product(id=ProductId("p1"), name="Sel", slug=Slug("sel"), shelf_life=NonExpiring()))
    session.commit()

    expiration = session.execute(
        text("SELECT expiration_date FROM products WHERE id = 'p1'")
    ).scalar_one()
    assert expiration is None
