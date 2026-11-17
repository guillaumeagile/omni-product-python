import pytest

from omni_product.domain.model.errors import InvalidValueError
from omni_product.domain.model.transport import CarbonKilos, Distance, Kilos, TransportMode
from omni_product.domain.model.transport_carbon_metrics import TransportCarbonMetrics
from omni_product.domain.model.transport_request import TransportRequest


def test_transport_mode_accepts_each_mode_of_the_closed_list() -> None:
    for mode in ("truck", "train", "ship", "plane"):
        assert TransportMode.parse(mode) == TransportMode(mode)


@pytest.mark.parametrize("raw", ["", "   ", "boat", "Truck"])
def test_transport_mode_rejects_anything_outside_the_closed_list(raw: str) -> None:
    with pytest.raises(InvalidValueError, match="TransportMode doit être l'un de"):
        TransportMode.parse(raw)


def test_distance_accepts_zero_and_rejects_negative() -> None:
    assert Distance(0.0).value == 0.0
    with pytest.raises(InvalidValueError, match="Distance ne peut pas être négatif"):
        Distance(-1.0)


def test_valid_request() -> None:
    request = TransportRequest(TransportMode.parse("truck"), Distance(120.0), Kilos(3.5))

    assert request.transport_mode == TransportMode("truck")
    assert request.distance_km.value == 120.0
    assert request.weight_kg.value == 3.5


@pytest.mark.parametrize(
    ("distance", "weight", "message"),
    [
        (0.0, 1.0, "Distance must be positive"),
        (1.0, 0.0, "Weight must be positive"),
        (1.0, -2.0, "ne peut pas être négatif"),
    ],
)
def test_invalid_request(distance: float, weight: float, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        TransportRequest(TransportMode.parse("truck"), Distance(distance), Kilos(weight))


def test_negative_metrics_are_rejected() -> None:
    with pytest.raises(ValueError, match="négatif"):
        TransportCarbonMetrics(
            CarbonKilos(-1.0), None, TransportMode.parse("truck"), Distance(10.0), Kilos(1.0)
        )
