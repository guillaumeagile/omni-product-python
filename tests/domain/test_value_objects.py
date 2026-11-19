"""Les Value Objects du domaine : égaux par valeur, ils refusent une valeur illégale."""

from collections.abc import Callable
from typing import Any

import pytest

from omni_product.domain.model import (
    Amount,
    CarbonEmission,
    Country,
    Distance,
    Email,
    Location,
    Phone,
    ProductId,
    Quantity,
    Region,
    ShelfLifeDays,
    Siren,
    Slug,
    SupplierId,
    TaxRate,
    TransportMode,
    TvaId,
    Volume,
    Weight,
)

_TEXTS: list[tuple[Callable[[str], Any], str]] = [
    (ProductId, "Product id is required"),
    (SupplierId, "Supplier id is required"),
    (Slug, "Slug is required"),
    (Location, "Location is required"),
    (Phone, "Phone is required"),
    (Country, "Country is required"),
    (Region, "Region is required"),
    (Siren, "Siren is required"),
    (TvaId, "TVA id is required"),
    (TransportMode, "Transport mode is required"),
    (Volume, "Volume is required"),
]

_NON_NEGATIVES: list[tuple[Callable[[Any], Any], str]] = [
    (Amount, "Amount cannot be negative"),
    (Quantity, "Quantity cannot be negative"),
    (ShelfLifeDays, "Shelf life cannot be negative"),
    (Weight, "Weight cannot be negative"),
    (Distance, "Distance cannot be negative"),
    (CarbonEmission, "Carbon emission cannot be negative"),
]


@pytest.mark.parametrize(("make", "message"), _TEXTS)
def test_text_value_keeps_its_text(make: Callable[[str], Any], message: str) -> None:
    assert make("x").value == "x"
    assert make("x") == make("x")


@pytest.mark.parametrize(("make", "message"), _TEXTS)
@pytest.mark.parametrize("blank", ["", "   "])
def test_text_value_rejects_blank(make: Callable[[str], Any], message: str, blank: str) -> None:
    with pytest.raises(ValueError, match=rf"^{message}$"):
        make(blank)


@pytest.mark.parametrize(("make", "message"), _NON_NEGATIVES)
def test_number_value_accepts_zero(make: Callable[[Any], Any], message: str) -> None:
    assert make(0).value == 0


@pytest.mark.parametrize(("make", "message"), _NON_NEGATIVES)
def test_number_value_rejects_negative(make: Callable[[Any], Any], message: str) -> None:
    with pytest.raises(ValueError, match=rf"^{message}$"):
        make(-1)


@pytest.mark.parametrize("rate", [0.0, 0.2, 1.0])
def test_tax_rate_between_zero_and_one_is_accepted(rate: float) -> None:
    assert TaxRate(rate).value == rate


@pytest.mark.parametrize("rate", [-0.01, 1.01])
def test_tax_rate_outside_zero_and_one_is_rejected(rate: float) -> None:
    with pytest.raises(ValueError, match=r"^Tax rate must be between 0 and 1$"):
        TaxRate(rate)


def test_email_needs_an_at_sign() -> None:
    assert Email("a@b.fr").value == "a@b.fr"
    with pytest.raises(ValueError, match=r"^Email must contain '@'$"):
        Email("ab.fr")
