import pytest

from omni_product.anemic_model import (
    Amount,
    ContactEmail,
    ContactPhone,
    Country,
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
from omni_product.anemic_model.errors import InvalidValueError

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
    Country,
    ContactEmail,
    ContactPhone,
]


@pytest.mark.parametrize("value_class", TEXT_VALUES)
def test_a_text_value_is_kept_when_it_has_content(value_class: type) -> None:
    assert value_class("abc").value == "abc"


@pytest.mark.parametrize("value_class", TEXT_VALUES)
@pytest.mark.parametrize("blank", ["", " ", "\t\n"])
def test_a_text_value_cannot_be_blank(value_class: type, blank: str) -> None:
    with pytest.raises(InvalidValueError, match=f"^{value_class.__name__} ne peut pas être vide$"):
        value_class(blank)


@pytest.mark.parametrize("value_class", [Amount, Kilos, Quantity, Stock])
def test_a_quantity_can_be_zero(value_class: type) -> None:
    assert value_class(0).value == 0


@pytest.mark.parametrize("value_class", [Amount, Kilos, Quantity, Stock])
def test_a_quantity_cannot_be_negative(value_class: type) -> None:
    with pytest.raises(
        InvalidValueError, match=f"^{value_class.__name__} ne peut pas être négatif$"
    ):
        value_class(-0.01)


@pytest.mark.parametrize("value", [0.0, 0.5, 1.0])
def test_a_rate_is_between_zero_and_one(value: float) -> None:
    assert Rate(value).value == value


@pytest.mark.parametrize("value", [-0.01, 1.01])
def test_a_rate_outside_zero_and_one_is_refused(value: float) -> None:
    with pytest.raises(InvalidValueError, match=r"^Rate doit être entre 0 et 1$"):
        Rate(value)


def test_invalid_value_is_a_value_error() -> None:
    # Les appels existants qui attrapent ValueError continuent de fonctionner.
    assert issubclass(InvalidValueError, ValueError)
