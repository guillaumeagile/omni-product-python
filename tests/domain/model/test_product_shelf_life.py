from datetime import date

from result import Ok

from omni_product.domain.model.product import (
    NonExpiring,
    ParDateEtDuree,
    ParDateLimite,
    ParDureeDeConservation,
    ShelfLifeDays,
    date_limite,
    perissable_of,
)

LIMITE = date(2026, 12, 1)
MSG_PERISSABLE = "Un produit périssable a une date limite ou une durée"


def test_shelf_life_days_accepts_zero_and_refuses_negative() -> None:
    assert ShelfLifeDays.of(0) == Ok(ShelfLifeDays(0))
    assert ShelfLifeDays.of(-1).is_err()


def test_date_limite_comes_from_perishable_variants_that_have_one() -> None:
    assert date_limite(ParDateLimite(LIMITE)) == LIMITE
    assert date_limite(ParDateEtDuree(LIMITE, ShelfLifeDays(7))) == LIMITE


def test_date_limite_is_none_without_date() -> None:
    assert date_limite(ParDureeDeConservation(ShelfLifeDays(7))) is None
    assert date_limite(NonExpiring()) is None
    assert date_limite(None) is None


def test_perishable_needs_a_date_or_a_duration() -> None:
    assert str(perissable_of(None, None).unwrap_err()) == MSG_PERISSABLE


def test_perishable_with_only_a_date() -> None:
    assert perissable_of(LIMITE, None) == Ok(ParDateLimite(LIMITE))


def test_perishable_with_only_a_duration() -> None:
    assert perissable_of(None, 7) == Ok(ParDureeDeConservation(ShelfLifeDays(7)))


def test_perishable_with_date_and_duration() -> None:
    assert perissable_of(LIMITE, 7) == Ok(ParDateEtDuree(LIMITE, ShelfLifeDays(7)))


def test_negative_duration_is_refused_with_or_without_date() -> None:
    assert perissable_of(None, -1).is_err()
    assert perissable_of(LIMITE, -1).is_err()
