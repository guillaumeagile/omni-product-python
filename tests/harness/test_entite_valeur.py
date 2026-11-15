"""La règle 2 (entité ou Value Object) sur de petits exemples dont on connaît la réponse."""

import textwrap

from harness.rules import entite_valeur
from harness.rules.sources import Source
from harness.rules.vocabulary import Vocabulary


def source(text: str, module: str = "pkg.mod") -> Source:
    return Source.from_text(module, textwrap.dedent(text))


def vocabulary() -> Vocabulary:
    return Vocabulary.load()


def codes(text: str) -> list[str]:
    return [finding.code for finding in entite_valeur.check(source(text), vocabulary())]


def test_a_frozen_dataclass_without_id_is_a_value_object():
    text = """
        from dataclasses import dataclass

        @dataclass(frozen=True)
        class Price:
            amount: float
        """
    assert codes(text) == []


def test_an_entity_with_a_dedicated_id_type_is_valid():
    text = """
        class Product:
            id: ProductId
            slug: Slug
        """
    assert codes(text) == []


def test_an_entity_with_a_primitive_id_is_a_violation():
    text = """
        class Product:
            id: str
        """
    [finding] = entite_valeur.check(source(text, "pkg.product"), vocabulary())
    assert finding.code == "EV001"
    assert str(finding) == (
        "pkg/product.py:2:1: EV001 'Product' a un identifiant de type primitif (str) : "
        "une entité porte un type dédié, comme ProductId"
    )


def test_a_mapped_primitive_id_is_still_primitive():
    text = """
        class Product(Base):
            id: Mapped[str] = mapped_column(primary_key=True)
        """
    assert codes(text) == ["EV001"]


def test_a_plain_class_without_id_is_neither_entity_nor_value_object():
    text = """
        class Shelf:
            capacity: int
        """
    assert codes(text) == ["EV001"]


def test_a_non_frozen_dataclass_without_id_is_a_violation():
    text = """
        from dataclasses import dataclass

        @dataclass
        class Price:
            amount: float
        """
    assert codes(text) == ["EV001"]


def test_a_subclass_inherits_the_id_of_its_entity():
    text = """
        class Product:
            id: ProductId

        class PerishableProduct(Product):
            shelf_life_days: int
        """
    assert codes(text) == []


def test_enums_protocols_and_exceptions_are_exempt():
    text = """
        from enum import Enum

        class Kind(Enum):
            FOOD = "food"

        class OutOfStockError(Exception):
            pass
        """
    assert codes(text) == []


def test_a_domain_primitive_in_a_raw_type_is_flagged():
    text = """
        from dataclasses import dataclass

        @dataclass(frozen=True)
        class Pricing:
            price: float
            slug: str
        """
    findings = entite_valeur.check(source(text, "pkg.pricing"), vocabulary())
    assert [(f.code, f.message) for f in findings] == [
        (
            "EV002",
            "'Pricing' porte 'price' (Pricing) en type primitif (float) "
            ": un Value Object est attendu",
        ),
        (
            "EV002",
            "'Pricing' porte 'slug' (Catalog) en type primitif (str) : un Value Object est attendu",
        ),
    ]


def test_a_domain_value_typed_by_a_value_object_is_not_flagged():
    text = """
        from dataclasses import dataclass

        @dataclass(frozen=True)
        class Pricing:
            price: Price
        """
    assert codes(text) == []


def test_a_link_and_a_name_outside_the_vocabulary_are_not_primitive_findings():
    text = """
        from dataclasses import dataclass

        @dataclass(frozen=True)
        class ProductDiscount:
            product_id: str
            name: str
        """
    assert codes(text) == []
