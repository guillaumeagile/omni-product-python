"""Les règles maison du harnais, sur de petits exemples dont on connaît la réponse."""

import textwrap

from harness.rules import contexte_borne
from harness.rules.sources import Source
from harness.rules.vocabulary import Vocabulary, words


def source(text: str, module: str = "pkg.mod") -> Source:
    return Source.from_text(module, textwrap.dedent(text))


def vocabulary() -> Vocabulary:
    return Vocabulary.load()


def test_names_are_split_into_folded_lowercase_words():
    assert words("getProductSlug") == ("get", "product", "slug")
    assert words("product_slug") == ("product", "slug")
    assert words("Products") == ("product",)
    # Un mot qui finit en « ss » n'est pas un pluriel.
    assert words("Address") == ("address",)


def test_a_name_is_matched_to_the_context_of_its_keyword():
    vocab = vocabulary()
    assert vocab.concern_of("fetchSlug") == "Catalog"
    assert vocab.concern_of("tvaId") == "Supplier"
    assert vocab.concern_of("kilos") == "Transport"
    assert vocab.concern_of("Id") is None
    assert vocab.concern_of("name") is None


def test_the_most_specific_keyword_wins():
    # « reseller » est Sales ; « ResellerPrice », plus précis, est Pricing.
    assert vocabulary().concern_of("resellerPrice") == "Pricing"


def test_a_weak_context_only_counts_when_nothing_else_matches():
    # « product » est un contexte faible (Catalog) : « price » (Pricing, fort) l'emporte.
    assert vocabulary().concern_of("productPrice") == "Pricing"
    assert vocabulary().concern_of("productName") == "Catalog"


def test_a_class_on_one_context_is_not_a_violation():
    text = """
        class Product:
            slug: str
            description: str

            def fetch_slug(self) -> str: ...
        """
    assert contexte_borne.check(source(text), vocabulary()) == []


def test_a_class_mixing_two_strong_contexts_is_a_violation():
    text = """
        class Product:
            slug: str
            price: float
        """
    [violation] = contexte_borne.check(source(text, "pkg.product"), vocabulary())
    assert violation.cls == "Product"
    assert violation.line == 2
    assert violation.members_by_concern == {"Catalog": ("slug",), "Pricing": ("price",)}


def test_the_context_of_an_untyped_name_comes_from_its_annotations():
    # `make` ne contient aucun mot-clé : c'est son paramètre `Warehouse` qui le rattache à Storage.
    text = """
        class Shelf:
            price: float

            def make(self, warehouse: Warehouse) -> None: ...
        """
    [violation] = contexte_borne.check(source(text), vocabulary())
    assert violation.members_by_concern == {"Pricing": ("price",), "Storage": ("make",)}


def test_a_violation_is_printed_like_a_ruff_diagnostic():
    text = """
        class Product:
            slug: str
            price: float
        """
    [violation] = contexte_borne.check(source(text, "pkg.product"), vocabulary())
    assert str(violation) == (
        "pkg/product.py:2:1: CB001 'Product' mêle 2 contextes : slug (Catalog), price (Pricing)"
    )


def test_private_members_are_not_part_of_the_context():
    text = """
        class Product:
            slug: str
            _price: float

            def _to_price(self) -> float: ...
        """
    assert contexte_borne.check(source(text), vocabulary()) == []
