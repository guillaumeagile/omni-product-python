import httpx
from result import Err, Ok, Result

from omni_product.domain.model.errors import ErreurTransport, InvalidValueError
from omni_product.domain.model.invariants import optionnel, premiere_erreur
from omni_product.domain.model.transport import CarbonKilos, Distance, Kilos, TransportMode
from omni_product.domain.model.transport_carbon_metrics import TransportCarbonMetrics
from omni_product.domain.model.transport_request import TransportRequest
from omni_product.infrastructure.adapter.impact_co2_api_client import ImpactCo2ApiClient
from omni_product.infrastructure.adapter.impact_co2_dtos import ImpactCo2Request, ImpactCo2Response


class ImpactCo2TransportAdapter:
    """Implémente `TransportCarbonPort`. Les échecs du service externe sont rendus comme valeurs."""

    def __init__(self, api_client: ImpactCo2ApiClient) -> None:
        self._api_client = api_client

    def calculate_emissions(
        self, transport_request: TransportRequest
    ) -> Result[TransportCarbonMetrics, ErreurTransport]:
        try:
            api_response = self._api_client.calculate_emissions(
                self._map_to_api_request(transport_request)
            )
        except httpx.HTTPError as e:
            return Err(ErreurTransport(f"Failed to calculate transport emissions: {e}"))
        except Exception as e:
            return Err(ErreurTransport(f"Unexpected error during carbon calculation: {e}"))
        # Une réponse dont les valeurs ne passent pas le domaine relève de l'infrastructure : c'est
        # une erreur du service externe, rendue avec les autres erreurs de calcul.
        match self._map_to_domain_model(api_response):
            case Ok(metrics):
                return Ok(metrics)
            case Err(erreur):
                return Err(ErreurTransport(f"Unexpected error during carbon calculation: {erreur}"))

    @staticmethod
    def _map_to_api_request(transport_request: TransportRequest) -> ImpactCo2Request:
        return ImpactCo2Request(
            transport_mode=transport_request.transport_mode.value,
            distance_km=transport_request.distance_km.value,
            weight_kg=transport_request.weight_kg.value,
        )

    @staticmethod
    def _map_to_domain_model(
        response: ImpactCo2Response,
    ) -> Result[TransportCarbonMetrics, InvalidValueError]:
        direct = response.co2_direct_kg
        match TransportMode.of(response.transport_mode):
            case Err(erreur):
                return Err(erreur)
            case Ok(mode):
                erreur = premiere_erreur(
                    [
                        CarbonKilos.of(response.co2_equivalent_kg),
                        optionnel(CarbonKilos.of, direct),
                        Distance.of(response.distance_km),
                        Kilos.of(response.weight_kg),
                    ]
                )
                if erreur is not None:
                    return Err(erreur)
                return Ok(
                    TransportCarbonMetrics(
                        co2_equivalent_kg=CarbonKilos(response.co2_equivalent_kg),
                        co2_direct_kg=None if direct is None else CarbonKilos(direct),
                        transport_mode=mode,
                        distance=Distance(response.distance_km),
                        weight=Kilos(response.weight_kg),
                    )
                )
