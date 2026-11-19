import pytest

from omni_product.domain.model.transport_carbon_metrics import TransportCarbonMetrics
from omni_product.domain.model.transport_request import TransportRequest


def test_valid_request() -> None:
    request = TransportRequest("truck", 120.0, 3.5)

    assert request.transport_mode == "truck"


def test_small_positive_distance_and_weight_are_accepted() -> None:
    request = TransportRequest("truck", 0.5, 0.5)

    assert (request.distance_km, request.weight_kg) == (0.5, 0.5)


@pytest.mark.parametrize(
    ("mode", "distance", "weight", "message"),
    [
        ("", 1.0, 1.0, "Transport mode is required"),
        ("   ", 1.0, 1.0, "Transport mode is required"),
        ("truck", 0.0, 1.0, "Distance must be positive"),
        ("truck", -1.0, 1.0, "Distance must be positive"),
        ("truck", 1.0, 0.0, "Weight must be positive"),
        ("truck", 1.0, -2.0, "Weight must be positive"),
    ],
)
def test_invalid_request(mode: str, distance: float, weight: float, message: str) -> None:
    with pytest.raises(ValueError, match=rf"^{message}$"):
        TransportRequest(mode, distance, weight)


@pytest.mark.parametrize(
    ("co2", "distance", "weight"),
    [(-1.0, 10.0, 1.0), (1.0, -10.0, 1.0), (1.0, 10.0, -1.0)],
)
def test_negative_metrics_are_rejected(co2: float, distance: float, weight: float) -> None:
    with pytest.raises(ValueError, match=r"^Carbon metrics cannot be negative$"):
        TransportCarbonMetrics(co2, None, "truck", distance, weight)


def test_zero_metrics_are_accepted() -> None:
    metrics = TransportCarbonMetrics(0.0, None, "truck", 0.0, 0.0)

    assert metrics.co2_equivalent_kg == 0.0
