import pytest

from omni_product.domain.model.transport import CarbonKilos, Distance, Kilos, TransportMode
from omni_product.domain.model.transport_request import TransportRequest


def test_transport_mode_accepts_each_mode_of_the_closed_list() -> None:
    for mode in ("truck", "train", "ship", "plane"):
        assert TransportMode.of(mode).unwrap() == TransportMode(mode)


@pytest.mark.parametrize("raw", ["", "   ", "boat", "Truck"])
def test_transport_mode_rejects_anything_outside_the_closed_list(raw: str) -> None:
    result = TransportMode.of(raw)

    assert result.is_err()
    assert str(result.unwrap_err()).startswith("TransportMode doit être l'un de")


def test_distance_accepts_zero_and_rejects_negative() -> None:
    assert Distance.of(0.0).unwrap().value == 0.0
    result = Distance.of(-1.0)
    assert result.is_err()
    assert str(result.unwrap_err()) == "Distance ne peut pas être négatif"


def test_valid_request() -> None:
    result = TransportRequest.of(TransportMode("truck"), Distance(120.0), Kilos(3.5))

    assert result.is_ok()
    request = result.unwrap()
    assert request.transport_mode == TransportMode("truck")
    assert request.distance_km.value == 120.0
    assert request.weight_kg.value == 3.5


@pytest.mark.parametrize(
    ("distance", "weight", "message"),
    [
        (0.0, 1.0, "Distance must be positive"),
        (1.0, 0.0, "Weight must be positive"),
    ],
)
def test_invalid_request_is_an_error_value(distance: float, weight: float, message: str) -> None:
    result = TransportRequest.of(TransportMode("truck"), Distance(distance), Kilos(weight))

    assert result.is_err()
    assert str(result.unwrap_err()) == message


def test_negative_weight_is_refused_by_the_value_object() -> None:
    result = Kilos.of(-2.0)

    assert result.is_err()
    assert str(result.unwrap_err()) == "Kilos ne peut pas être négatif"


def test_negative_metrics_are_rejected() -> None:
    result = CarbonKilos.of(-1.0)

    assert result.is_err()
    assert "négatif" in str(result.unwrap_err())
