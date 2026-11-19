from datetime import date

from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from omni_product.domain.model.product import NonExpiringProduct, PerishableProduct, Product
from omni_product.domain.model.product_values import (
    ExpirationDate,
    ProductId,
    ProductName,
    ShelfLifeDays,
    Slug,
)


def _product(cls: type[Product], id: str, name: str, slug: str) -> Product:
    return cls(id=ProductId(id), name=ProductName(name), slug=Slug(slug))


def test_is_perishable_is_true_only_for_perishable_products() -> None:
    assert _product(PerishableProduct, "p1", "Lait", "lait").is_perishable()
    assert not _product(NonExpiringProduct, "p2", "Sel", "sel").is_perishable()
    assert not _product(Product, "p3", "Stylo", "stylo").is_perishable()


def test_perishable_fields_are_optional_in_memory() -> None:
    product = PerishableProduct(id=ProductId("p1"), name=ProductName("Lait"), slug=Slug("lait"))

    assert product.expiration_date is None
    assert product.shelf_life_days is None


def test_kind_is_written_from_the_python_class(session: Session) -> None:
    session.add_all(
        [
            _product(Product, "p1", "Stylo", "stylo"),
            _product(PerishableProduct, "p2", "Lait", "lait"),
            _product(NonExpiringProduct, "p3", "Sel", "sel"),
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
                name=ProductName("Lait"),
                slug=Slug("lait"),
                expiration_date=ExpirationDate(date(2026, 12, 1)),
                shelf_life_days=ShelfLifeDays(7),
            )
        )
        writer.commit()

    # Une session neuve : on recharge la ligne au lieu de réutiliser l'objet en mémoire.
    with app.state.session_factory() as reader:
        loaded = reader.get(Product, ProductId("p1"))

        assert isinstance(loaded, PerishableProduct)
        assert loaded.expiration_date == ExpirationDate(date(2026, 12, 1))
        assert loaded.shelf_life_days == ShelfLifeDays(7)
        assert loaded.is_perishable()


def test_single_table_leaves_perishable_columns_null_for_other_kinds(session: Session) -> None:
    session.add(_product(NonExpiringProduct, "p1", "Sel", "sel"))
    session.commit()

    expiration = session.execute(
        text("SELECT expiration_date FROM products WHERE id = 'p1'")
    ).scalar_one()
    assert expiration is None
