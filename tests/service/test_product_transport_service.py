from result import Ok, Result

from omni_product.domain.model.errors import ErreurTransport
from omni_product.domain.model.transport import CarbonKilos, Distance, Kilos, TransportMode
from omni_product.domain.model.transport_carbon_metrics import TransportCarbonMetrics
from omni_product.domain.model.transport_request import TransportRequest
from omni_product.service.product_transport_service import ProductTransportService


class FakePort:
    def __init__(self) -> None:
        self.received: TransportRequest | None = None

    def calculate_emissions(
        self, transport_request: TransportRequest
    ) -> Result[TransportCarbonMetrics, ErreurTransport]:
        self.received = transport_request
        return Ok(
            TransportCarbonMetrics(
                CarbonKilos(2.5),
                CarbonKilos(2.0),
                transport_request.transport_mode,
                transport_request.distance_km,
                transport_request.weight_kg,
            )
        )


def test_delegates_to_the_port() -> None:
    port = FakePort()

    metrics = ProductTransportService(port).calculate_shipment_carbon("truck", 100.0, 5.0).unwrap()

    assert port.received == TransportRequest(TransportMode("truck"), Distance(100.0), Kilos(5.0))
    assert metrics.co2_equivalent_kg == CarbonKilos(2.5)


def test_rejects_an_unknown_mode_before_calling_the_port() -> None:
    port = FakePort()

    result = ProductTransportService(port).calculate_shipment_carbon("boat", 100.0, 5.0)

    assert result.is_err()
    assert str(result.unwrap_err()).startswith("TransportMode doit être l'un de")
    assert port.received is None


def test_rejects_invalid_request_before_calling_the_port() -> None:
    port = FakePort()

    result = ProductTransportService(port).calculate_shipment_carbon("truck", 0.0, 5.0)

    assert result.is_err()
    assert str(result.unwrap_err()) == "Distance must be positive"
    assert port.received is None
