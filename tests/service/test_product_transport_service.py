import pytest

from omni_product.domain.model.transport_carbon_metrics import TransportCarbonMetrics
from omni_product.domain.model.transport_request import TransportRequest
from omni_product.service.product_transport_service import ProductTransportService


class FakePort:
    def __init__(self) -> None:
        self.received: TransportRequest | None = None

    def calculate_emissions(self, transport_request: TransportRequest) -> TransportCarbonMetrics:
        self.received = transport_request
        return TransportCarbonMetrics(
            2.5,
            2.0,
            transport_request.transport_mode,
            transport_request.distance_km,
            transport_request.weight_kg,
        )


def test_delegates_to_the_port() -> None:
    port = FakePort()

    metrics = ProductTransportService(port).calculate_shipment_carbon("truck", 100.0, 5.0)

    assert port.received == TransportRequest("truck", 100.0, 5.0)
    assert metrics.co2_equivalent_kg == 2.5


def test_rejects_invalid_request_before_calling_the_port() -> None:
    port = FakePort()

    with pytest.raises(ValueError, match="Distance must be positive"):
        ProductTransportService(port).calculate_shipment_carbon("truck", 0.0, 5.0)

    assert port.received is None
