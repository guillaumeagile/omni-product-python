from omni_product.domain.model.transport_carbon_metrics import TransportCarbonMetrics
from omni_product.domain.model.transport_request import TransportRequest
from omni_product.domain.port.transport_carbon_port import TransportCarbonPort


class ProductTransportService:
    def __init__(self, transport_carbon_port: TransportCarbonPort) -> None:
        self._transport_carbon_port = transport_carbon_port

    def calculate_shipment_carbon(
        self, transport_mode: str, distance_km: float, weight_kg: float
    ) -> TransportCarbonMetrics:
        request = TransportRequest(transport_mode, round(distance_km), weight_kg)
        return self._transport_carbon_port.calculate_emissions(request)
