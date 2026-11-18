"""La persistance des produits : ce que la base garde du modèle, et comment elle le rend."""

from datetime import date

from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from omni_product.dal import product_dal
from omni_product.dal.product_dal import ProductSheet
from omni_product.domain.model import (
    NonExpiring,
    Perishable,
    Product,
    ProductId,
    ShelfLifeDays,
    Slug,
)


def test_kind_is_written_from_the_shelf_life(session: Session) -> None:
    for product in (
        Product(id=ProductId("p1"), name="Stylo", slug=Slug("stylo")),
        Product(id=ProductId("p2"), name="Lait", slug=Slug("lait"), shelf_life=Perishable()),
        Product(id=ProductId("p3"), name="Sel", slug=Slug("sel"), shelf_life=NonExpiring()),
    ):
        product_dal.save(session, ProductSheet(product=product))

    kinds = dict(session.execute(text("SELECT id, kind FROM products ORDER BY id")).all())
    assert kinds == {"p1": "standard", "p2": "perishable", "p3": "non_expiring"}


def test_row_is_loaded_back_with_its_shelf_life(app: FastAPI) -> None:
    with app.state.session_factory() as writer:
        product_dal.save(
            writer,
            ProductSheet(
                product=Product(
                    id=ProductId("p1"),
                    name="Lait",
                    slug=Slug("lait"),
                    shelf_life=Perishable(
                        expiration_date=date(2026, 12, 1), shelf_life_days=ShelfLifeDays(7)
                    ),
                )
            ),
        )

    # Une session neuve : on recharge la ligne au lieu de réutiliser l'objet en mémoire.
    with app.state.session_factory() as reader:
        loaded = product_dal.find_by_id(reader, ProductId("p1"))

        assert loaded is not None
        product = loaded.product
        assert product.shelf_life == Perishable(
            expiration_date=date(2026, 12, 1), shelf_life_days=ShelfLifeDays(7)
        )
        assert product.is_perishable()


def test_single_table_leaves_perishable_columns_null_for_other_kinds(session: Session) -> None:
    product_dal.save(
        session,
        ProductSheet(
            product=Product(
                id=ProductId("p1"), name="Sel", slug=Slug("sel"), shelf_life=NonExpiring()
            )
        ),
    )

    expiration = session.execute(
        text("SELECT expiration_date FROM products WHERE id = 'p1'")
    ).scalar_one()
    assert expiration is None
