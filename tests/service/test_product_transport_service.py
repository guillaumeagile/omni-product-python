import pytest

from omni_product.domain.model.transport_carbon_metrics import TransportCarbonMetrics
from omni_product.domain.model.transport_request import TransportRequest
from omni_product.domain.model.transport_values import (
    CarbonEmission,
    Distance,
    TransportMode,
    Weight,
)
from omni_product.service.product_transport_service import ProductTransportService


class FakePort:
    def __init__(self) -> None:
        self.received: TransportRequest | None = None

    def calculate_emissions(self, transport_request: TransportRequest) -> TransportCarbonMetrics:
        self.received = transport_request
        return TransportCarbonMetrics(
            CarbonEmission(2.5),
            CarbonEmission(2.0),
            transport_request.transport_mode,
            transport_request.distance,
            transport_request.weight,
        )


def test_delegates_to_the_port() -> None:
    port = FakePort()

    metrics = ProductTransportService(port).calculate_shipment_carbon("truck", 100.0, 5.0)

    assert port.received == TransportRequest(TransportMode("truck"), Distance(100.0), Weight(5.0))
    assert metrics.carbon_equivalent == CarbonEmission(2.5)


def test_rejects_invalid_request_before_calling_the_port() -> None:
    port = FakePort()

    with pytest.raises(ValueError, match="Distance must be positive"):
        ProductTransportService(port).calculate_shipment_carbon("truck", 0.0, 5.0)

    assert port.received is None
