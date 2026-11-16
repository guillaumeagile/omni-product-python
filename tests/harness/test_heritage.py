"""La règle 4 : les variantes se composent, elles n'héritent pas les unes des autres."""

import textwrap

from harness.rules import heritage
from harness.rules.sources import Source
from harness.rules.ubiquitous_language import UbiquitousLanguage


def source(text: str) -> Source:
    return Source.from_text("omni_product.domain.model.product", textwrap.dedent(text))


def codes_of(text: str) -> list[tuple[str, str]]:
    return [(f.cls, f.code) for f in heritage.check(source(text), UbiquitousLanguage.load())]


def test_variants_inheriting_from_a_class_of_the_same_module_are_findings():
    text = """
        class Product: ...
        class PerishableProduct(Product): ...
        class NonExpiringProduct(Product): ...
        """

    assert codes_of(text) == [
        ("PerishableProduct", heritage.CODE),
        ("NonExpiringProduct", heritage.CODE),
    ]


def test_a_finding_names_the_parent_and_the_composition_to_use():
    [finding] = heritage.check(
        source("class Product: ...\nclass PerishableProduct(Product): ...\n"),
        UbiquitousLanguage.load(),
    )

    assert "`PerishableProduct` hérite de `Product`" in finding.message
    assert "se compose" in finding.message


def test_enums_protocols_typed_dicts_and_exceptions_are_exempt():
    text = """
        class Colour(Enum):
            RED = 1

        class Shade(Colour): ...

        class Repository(Protocol): ...

        class InMemoryRepository(Repository): ...

        class ProductError(ValueError): ...

        class StockError(ProductError): ...
        """

    assert codes_of(text) == []


def test_a_base_declared_in_another_module_is_not_seen():
    # `Base` (SQLAlchemy) vient d'un autre module : c'est la règle 3 qui le signale.
    assert codes_of("class Product(Base): ...\n") == []
