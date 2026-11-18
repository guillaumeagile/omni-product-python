"""La règle 7 : drapeau stocké et `None` par paires sont des constats."""

import textwrap

from harness.rules import etat_illegal
from harness.rules.sources import Source
from harness.rules.ubiquitous_language import UbiquitousLanguage


def source(text: str) -> Source:
    return Source.from_text("omni_product.domain.model.product", textwrap.dedent(text))


def findings_of(text: str) -> list[etat_illegal.Finding]:
    return etat_illegal.check(source(text), UbiquitousLanguage.load())


def codes_of(text: str) -> list[str]:
    return [f.code for f in findings_of(text)]


def test_a_stored_boolean_flag_is_a_finding():
    text = """
        class Product:
            is_perishable: bool
        """

    [finding] = findings_of(text)

    assert (finding.line, finding.col, finding.code) == (3, 5, etat_illegal.CODE_FLAG)
    assert "is_perishable" in finding.message


def test_has_prefix_and_optional_bool_are_flags_too():
    text = """
        class Product:
            has_discount: bool | None = None
        """

    assert codes_of(text) == [etat_illegal.CODE_FLAG]


def test_a_boolean_without_flag_prefix_is_not_a_finding():
    text = """
        class Product:
            active: bool
            is_perishable: str
        """

    assert codes_of(text) == []


def test_a_boolean_method_is_not_a_stored_flag():
    text = """
        class Product:
            def is_perishable(self) -> bool:
                return False
        """

    assert codes_of(text) == []


def test_two_optional_fields_in_a_class_are_one_finding():
    text = """
        from datetime import date

        class Perishable:
            expiration_date: date | None
            shelf_life_days: int | None
        """

    [finding] = findings_of(text)

    assert (finding.line, finding.code) == (4, etat_illegal.CODE_OPTIONALS)
    assert "expiration_date" in finding.message
    assert "shelf_life_days" in finding.message


def test_a_single_optional_field_is_not_a_finding():
    text = """
        class TransportCarbonMetrics:
            co2_equivalent_kg: float
            co2_direct_kg: float | None
        """

    assert codes_of(text) == []


def test_optional_and_union_spellings_are_all_read():
    text = """
        from typing import Optional, Union

        class A:
            first: Optional[int]
            second: Union[str, None]
            third: "int | None"
        """

    assert codes_of(text) == [etat_illegal.CODE_OPTIONALS]
    assert "2 champs" in findings_of(text)[0].message


def test_sqlalchemy_mapped_annotations_are_unwrapped():
    text = """
        class PerishableProduct:
            expiration_date: Mapped[date | None] = mapped_column(Date)
            shelf_life_days: Mapped[int | None] = mapped_column(Integer)
            name: Mapped[str] = mapped_column(String)
        """

    assert codes_of(text) == [etat_illegal.CODE_OPTIONALS]


def test_a_closed_union_of_frozen_dataclasses_is_clean():
    text = """
        from dataclasses import dataclass
        from datetime import date

        @dataclass(frozen=True)
        class Perishable:
            sell_by: date
            use_by: date

        @dataclass(frozen=True)
        class NonExpiring:
            best_before: date

        ShelfLife = Perishable | NonExpiring
        """

    assert codes_of(text) == []


def test_enums_protocols_and_exceptions_are_exempt():
    text = """
        class Kind(Enum):
            is_x: bool
            a: int | None
            b: int | None

        class Port(Protocol):
            a: int | None
            b: int | None

        class OutOfStockError(Exception):
            a: int | None
            b: int | None
        """

    assert codes_of(text) == []


def test_findings_come_in_line_order():
    text = """
        class A:
            a: int | None
            b: int | None

        class B:
            is_ok: bool
        """

    assert [f.line for f in findings_of(text)] == [2, 7]


def test_the_diagnostic_follows_the_ruff_format():
    [finding] = findings_of("class A:\n    is_ok: bool\n")

    assert str(finding).startswith("omni_product/domain/model/product.py:2:5: EL001 ")
