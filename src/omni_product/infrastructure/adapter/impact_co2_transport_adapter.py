import httpx

from omni_product.domain.exception.transport_carbon_exception import TransportCarbonException
from omni_product.domain.model.transport_carbon_metrics import TransportCarbonMetrics
from omni_product.domain.model.transport_request import TransportRequest
from omni_product.infrastructure.adapter.impact_co2_api_client import ImpactCo2ApiClient
from omni_product.infrastructure.adapter.impact_co2_dtos import ImpactCo2Request, ImpactCo2Response


class ImpactCo2TransportAdapter:
    """Implémente `TransportCarbonPort`."""

    def __init__(self, api_client: ImpactCo2ApiClient) -> None:
        self._api_client = api_client

    def calculate_emissions(self, transport_request: TransportRequest) -> TransportCarbonMetrics:
        try:
            api_response = self._api_client.calculate_emissions(
                self._map_to_api_request(transport_request)
            )
            return self._map_to_domain_model(api_response)
        except httpx.HTTPError as e:
            raise TransportCarbonException(f"Failed to calculate transport emissions: {e}") from e
        except Exception as e:
            raise TransportCarbonException(
                f"Unexpected error during carbon calculation: {e}"
            ) from e

    @staticmethod
    def _map_to_api_request(transport_request: TransportRequest) -> ImpactCo2Request:
        return ImpactCo2Request(
            transport_mode=transport_request.transport_mode,
            distance_km=transport_request.distance_km,
            weight_kg=transport_request.weight_kg,
        )

    @staticmethod
    def _map_to_domain_model(response: ImpactCo2Response) -> TransportCarbonMetrics:
        return TransportCarbonMetrics(
            co2_equivalent_kg=response.co2_equivalent_kg,
            co2_direct_kg=response.co2_direct_kg,
            transport_mode=response.transport_mode,
            distance=response.distance_km,
            weight=response.weight_kg,
        )
