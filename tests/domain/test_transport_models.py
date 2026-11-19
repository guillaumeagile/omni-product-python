import pytest

from omni_product.domain.model.transport import CarbonEmission, Distance, TransportMode, Weight
from omni_product.domain.model.transport_carbon_metrics import TransportCarbonMetrics
from omni_product.domain.model.transport_request import TransportRequest

TRUCK = TransportMode("truck")


def test_valid_request() -> None:
    request = TransportRequest(TRUCK, Distance(120.0), Weight(3.5))

    assert request.transport_mode == TRUCK


def test_small_positive_distance_and_weight_are_accepted() -> None:
    request = TransportRequest(TRUCK, Distance(0.5), Weight(0.5))

    assert (request.distance_km, request.weight_kg) == (Distance(0.5), Weight(0.5))


@pytest.mark.parametrize(
    ("distance", "weight", "message"),
    [
        (0.0, 1.0, "Distance must be positive"),
        (1.0, 0.0, "Weight must be positive"),
    ],
)
def test_zero_distance_or_weight_is_rejected(distance: float, weight: float, message: str) -> None:
    with pytest.raises(ValueError, match=rf"^{message}$"):
        TransportRequest(TRUCK, Distance(distance), Weight(weight))


def test_zero_metrics_are_accepted() -> None:
    metrics = TransportCarbonMetrics(CarbonEmission(0.0), None, TRUCK, Distance(0.0), Weight(0.0))

    assert metrics.co2_equivalent_kg == CarbonEmission(0.0)
