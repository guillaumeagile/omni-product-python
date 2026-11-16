"""Règle 1 : un identifiant ne porte pas de contexte, qu'il soit naturel ou non."""

import textwrap

from harness.rules import contexte_borne
from harness.rules.sources import Source
from harness.rules.ubiquitous_language import UbiquitousLanguage


def language() -> UbiquitousLanguage:
    return UbiquitousLanguage.load()


def source(text: str) -> Source:
    return Source.from_text("pkg.mod", textwrap.dedent(text))


def test_fields_starting_or_ending_with_id_are_identifiers():
    lang = language()

    for name in ("id", "product_id", "productId", "supplierIds", "tvaId", "idProduct"):
        assert lang.is_identifier(name), name


def test_words_that_only_contain_id_are_not_identifiers():
    lang = language()

    assert not lang.is_identifier("identity")
    assert not lang.is_identifier("discount")
    assert not lang.is_identifier("hidden")


def test_an_entity_keyed_by_its_product_id_is_not_mixing_contexts():
    # Le cas de ProductPrice : `id: ProductId` ne doit pas rattacher `id` à Catalog.
    text = """
        class ProductPrice:
            id: ProductId
            price: Price | None = None
            discounts: tuple[Discount, ...] = ()
        """

    assert contexte_borne.check(source(text), language()) == []


def test_a_mixed_class_is_still_a_violation_when_the_identifier_is_excluded():
    text = """
        class Product:
            id: ProductId
            slug: str
            price: float
        """

    [violation] = contexte_borne.check(source(text), language())
    assert violation.members_by_concern == {"Catalog": ("slug",), "Pricing": ("price",)}
