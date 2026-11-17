"""La règle 5 : tout `raise` dans le modèle est un constat, un échec en valeur n'en est pas un."""

import textwrap

from harness.rules import echec_valeur
from harness.rules.sources import Source
from harness.rules.ubiquitous_language import UbiquitousLanguage


def source(text: str) -> Source:
    return Source.from_text("omni_product.domain.model.product", textwrap.dedent(text))


def lines_of(text: str) -> list[int]:
    return [f.line for f in echec_valeur.check(source(text), UbiquitousLanguage.load())]


def test_a_raise_in_the_model_is_a_finding():
    text = """
        class TransportRequest:
            def __post_init__(self) -> None:
                if self.distance_km <= 0:
                    raise ValueError("Distance must be positive")
        """

    assert lines_of(text) == [5]


def test_every_raise_is_a_finding_with_its_position():
    text = """
        def withdraw(stock: int, quantity: int) -> int:
            if quantity > stock:
                raise ValueError("Insufficient stock")
            return stock - quantity

        def other() -> None:
            raise RuntimeError("boom")
        """
    [first, second] = echec_valeur.check(source(text), UbiquitousLanguage.load())

    assert (first.line, first.col, first.code) == (4, 9, echec_valeur.CODE)
    assert second.line == 8


def test_a_failure_returned_as_a_value_is_not_a_finding():
    text = """
        from dataclasses import dataclass

        @dataclass(frozen=True)
        class Withdrawn:
            remaining: int

        @dataclass(frozen=True)
        class InsufficientStock:
            missing: int

        def withdraw(stock: int, quantity: int) -> Withdrawn | InsufficientStock:
            if quantity > stock:
                return InsufficientStock(quantity - stock)
            return Withdrawn(stock - quantity)
        """

    assert lines_of(text) == []


def test_the_finding_names_the_fix():
    [finding] = echec_valeur.check(
        source("def f() -> None:\n    raise ValueError('x')\n"), UbiquitousLanguage.load()
    )

    assert "rendre l'échec comme valeur" in finding.message
