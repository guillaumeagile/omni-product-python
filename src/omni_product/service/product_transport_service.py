from result import Err, Ok, Result

from omni_product.domain.model.errors import InvalidValueError
from omni_product.domain.model.transport import Distance, Kilos, TransportMode
from omni_product.domain.model.transport_carbon_metrics import TransportCarbonMetrics
from omni_product.domain.model.transport_request import TransportRequest
from omni_product.domain.port.transport_carbon_port import TransportCarbonPort


class ProductTransportService:
    def __init__(self, transport_carbon_port: TransportCarbonPort) -> None:
        self._transport_carbon_port = transport_carbon_port

    def calculate_shipment_carbon(
        self, transport_mode: str, distance_km: float, weight_kg: float
    ) -> Result[TransportCarbonMetrics, InvalidValueError]:
        match TransportRequest.of(
            TransportMode.parse(transport_mode),
            Distance(round(distance_km)),
            Kilos(weight_kg),
        ):
            case Ok(request):
                return Ok(self._transport_carbon_port.calculate_emissions(request))
            case Err(erreur):
                return Err(erreur)
