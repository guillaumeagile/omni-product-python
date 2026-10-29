import httpx

from omni_product.infrastructure.adapter.impact_co2_dtos import ImpactCo2Request, ImpactCo2Response

TRANSPORT_ENDPOINT = "/transport/emissions"


class ImpactCo2ApiClient:
    """Le `RestTemplate` Java devient un `httpx.Client` injecté (timeouts réglés à sa création)."""

    def __init__(self, http_client: httpx.Client, base_url: str) -> None:
        self._http_client = http_client
        self._base_url = base_url

    def calculate_emissions(self, request: ImpactCo2Request) -> ImpactCo2Response:
        response = self._http_client.post(
            self._base_url + TRANSPORT_ENDPOINT, json=request.model_dump()
        )
        response.raise_for_status()
        return ImpactCo2Response.model_validate(response.json())
