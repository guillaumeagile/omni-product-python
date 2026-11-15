"""Les règles maison du harnais, sur de petits exemples dont on connaît la réponse."""

import textwrap

from harness.rules import contexte_borne
from harness.rules.sources import Source
from harness.rules.ubiquitous_language import UbiquitousLanguage, words


def source(text: str, module: str = "pkg.mod") -> Source:
    return Source.from_text(module, textwrap.dedent(text))


def language() -> UbiquitousLanguage:
    return UbiquitousLanguage.load()


def test_names_are_split_into_folded_lowercase_words():
    assert words("getProductSlug") == ("get", "product", "slug")
    assert words("product_slug") == ("product", "slug")
    assert words("Products") == ("product",)
    # Un mot qui finit en « ss » n'est pas un pluriel.
    assert words("Address") == ("address",)


def test_a_name_is_matched_to_the_context_of_its_keyword():
    lang = language()
    assert lang.concern_of("fetchSlug") == "Catalog"
    assert lang.concern_of("tvaId") == "Supplier"
    assert lang.concern_of("kilos") == "Transport"
    assert lang.concern_of("Id") is None
    assert lang.concern_of("name") is None


def test_the_most_specific_keyword_wins():
    # « reseller » est Sales ; « ResellerPrice », plus précis, est Pricing.
    assert language().concern_of("resellerPrice") == "Pricing"


def test_a_weak_context_only_counts_when_nothing_else_matches():
    # « product » est un contexte faible (Catalog) : « price » (Pricing, fort) l'emporte.
    assert language().concern_of("productPrice") == "Pricing"
    assert language().concern_of("productName") == "Catalog"


def test_a_class_on_one_context_is_not_a_violation():
    text = """
        class Product:
            slug: str
            description: str

            def fetch_slug(self) -> str: ...
        """
    assert contexte_borne.check(source(text), language()) == []


def test_a_class_mixing_two_strong_contexts_is_a_violation():
    text = """
        class Product:
            slug: str
            price: float
        """
    [violation] = contexte_borne.check(source(text, "pkg.product"), language())
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
    [violation] = contexte_borne.check(source(text), language())
    assert violation.members_by_concern == {"Pricing": ("price",), "Storage": ("make",)}


def test_a_violation_is_printed_like_a_ruff_diagnostic():
    text = """
        class Product:
            slug: str
            price: float
        """
    [violation] = contexte_borne.check(source(text, "pkg.product"), language())
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
    assert contexte_borne.check(source(text), language()) == []


def test_a_link_identifier_is_not_a_context():
    lang = language()
    assert lang.is_link("product_id")
    assert lang.is_link("supplierIds")
    # Un identifiant naturel est une donnée (TVA), pas un lien. `id` seul n'est pas un lien.
    assert not lang.is_link("tvaId")
    assert not lang.is_link("id")
    assert not lang.is_link("discount")


def test_a_row_linked_to_its_product_by_id_is_one_context():
    # Le lien `product_id` ne compte pas : la classe ne porte que le contexte Pricing.
    text = """
        class ProductDiscount:
            product_id: str
            discount: str
        """
    assert contexte_borne.check(source(text), language()) == []


def test_inherited_members_count_towards_the_contexts_of_the_subclass():
    text = """
        class Product:
            slug: str

        class PricedProduct(Product):
            price: float
        """
    [violation] = contexte_borne.check(source(text, "pkg.product"), language())
    assert violation.cls == "PricedProduct"
    assert violation.members_by_concern == {"Catalog": ("slug",), "Pricing": ("price",)}


def test_an_overridden_member_keeps_the_subclass_version():
    text = """
        class Product:
            price: float

        class Shelf(Product):
            price: str
        """
    assert contexte_borne.check(source(text), language()) == []


def test_a_word_outside_the_ubiquitous_language_is_a_gap():
    text = """
        class Shelf:
            rating: int
        """
    [gap] = contexte_borne.gaps(source(text, "pkg.shelf"), language())
    assert gap.unknown == (("rating", ("rating",)),)
    assert str(gap) == (
        "pkg/shelf.py:2:1: CB002 'Shelf' a des mots hors ubiquitous language : rating (rating)"
    )


def test_generic_names_and_linked_or_known_members_are_not_gaps():
    text = """
        class Shelf:
            id: str
            name: str
            product_id: str
            slug: str

            def get_count(self) -> int: ...

            def make(self, warehouse: Warehouse) -> None: ...
        """
    assert contexte_borne.gaps(source(text), language()) == []


def test_inherited_gaps_are_reported_in_their_own_class_only():
    text = """
        class Base:
            rating: int

        class Child(Base):
            pass
        """
    [gap] = contexte_borne.gaps(source(text), language())
    assert gap.cls == "Base"


def test_a_violation_is_not_changed_by_the_gaps_check():
    text = """
        class Product:
            slug: str
            price: float
            rating: int
        """
    [violation] = contexte_borne.check(source(text, "pkg.product"), language())
    assert violation.members_by_concern == {"Catalog": ("slug",), "Pricing": ("price",)}
