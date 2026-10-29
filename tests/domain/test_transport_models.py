import pytest

from omni_product.domain.model.transport_carbon_metrics import TransportCarbonMetrics
from omni_product.domain.model.transport_request import TransportRequest


def test_valid_request() -> None:
    request = TransportRequest("truck", 120.0, 3.5)

    assert request.transport_mode == "truck"


@pytest.mark.parametrize(
    ("mode", "distance", "weight", "message"),
    [
        ("", 1.0, 1.0, "Transport mode is required"),
        ("   ", 1.0, 1.0, "Transport mode is required"),
        ("truck", 0.0, 1.0, "Distance must be positive"),
        ("truck", 1.0, -2.0, "Weight must be positive"),
    ],
)
def test_invalid_request(mode: str, distance: float, weight: float, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        TransportRequest(mode, distance, weight)


def test_negative_metrics_are_rejected() -> None:
    with pytest.raises(ValueError, match="cannot be negative"):
        TransportCarbonMetrics(-1.0, None, "truck", 10.0, 1.0)
