from typing import Any

import pytest

from omni_product.domain.model import (
    Amount,
    Discount,
    ImageDetail,
    ImageKey,
    Kilos,
    Location,
    ProductId,
    Quantity,
    Rate,
    Region,
    Siren,
    Slug,
    Stock,
    SupplierId,
    TvaId,
    Volume,
)
from omni_product.kernel.errors import InvalidValueError

TEXT_VALUES = [
    ProductId,
    Slug,
    ImageKey,
    ImageDetail,
    Discount,
    Location,
    Volume,
    Region,
    SupplierId,
    Siren,
    TvaId,
]


@pytest.mark.parametrize("value_class", TEXT_VALUES)
def test_a_text_value_is_kept_when_it_has_content(value_class: Any) -> None:
    result = value_class.of("abc")

    assert result.is_ok()
    assert result.unwrap().value == "abc"


@pytest.mark.parametrize("value_class", TEXT_VALUES)
@pytest.mark.parametrize("blank", ["", " ", "\t\n"])
def test_a_text_value_cannot_be_blank(value_class: Any, blank: str) -> None:
    result = value_class.of(blank)

    assert result.is_err()
    assert str(result.unwrap_err()) == f"{value_class.__name__} ne peut pas être vide"


@pytest.mark.parametrize("value_class", [Amount, Kilos, Quantity, Stock])
def test_a_quantity_can_be_zero(value_class: Any) -> None:
    assert value_class.of(0).unwrap().value == 0


@pytest.mark.parametrize("value_class", [Amount, Kilos, Quantity, Stock])
def test_a_quantity_cannot_be_negative(value_class: Any) -> None:
    result = value_class.of(-0.01)

    assert result.is_err()
    assert str(result.unwrap_err()) == f"{value_class.__name__} ne peut pas être négatif"


@pytest.mark.parametrize("value", [0.0, 0.5, 1.0])
def test_a_rate_is_between_zero_and_one(value: float) -> None:
    assert Rate.of(value).unwrap().value == value


@pytest.mark.parametrize("value", [-0.01, 1.01])
def test_a_rate_outside_zero_and_one_is_refused(value: float) -> None:
    result = Rate.of(value)

    assert result.is_err()
    assert str(result.unwrap_err()) == "Rate doit être entre 0 et 1"


def test_invalid_value_is_a_value_error() -> None:
    # Les appels existants qui attrapent ValueError continuent de fonctionner.
    assert issubclass(InvalidValueError, ValueError)
