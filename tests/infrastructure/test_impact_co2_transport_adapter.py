import json

import httpx
import pytest

from omni_product.domain.exception.transport_carbon_exception import TransportCarbonException
from omni_product.domain.model.transport_request import TransportRequest
from omni_product.infrastructure.adapter.impact_co2_api_client import ImpactCo2ApiClient
from omni_product.infrastructure.adapter.impact_co2_transport_adapter import (
    ImpactCo2TransportAdapter,
)

BASE_URL = "https://impactco2.test/api/v1"


def _adapter(handler: httpx.MockTransport) -> ImpactCo2TransportAdapter:
    client = ImpactCo2ApiClient(httpx.Client(transport=handler), BASE_URL)
    return ImpactCo2TransportAdapter(client)


def test_maps_request_and_response() -> None:
    seen: dict[str, object] = {}

    def handle(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "co2_equivalent_kg": 4.2,
                "co2_direct_kg": 3.9,
                "transport_mode": "truck",
                "distance_km": 100.0,
                "weight_kg": 5.0,
            },
        )

    metrics = _adapter(httpx.MockTransport(handle)).calculate_emissions(
        TransportRequest("truck", 100.0, 5.0)
    )

    assert seen["url"] == f"{BASE_URL}/transport/emissions"
    assert seen["body"] == {"transport_mode": "truck", "distance_km": 100.0, "weight_kg": 5.0}
    assert metrics.co2_equivalent_kg == 4.2
    assert metrics.co2_direct_kg == 3.9
    assert metrics.distance == 100.0
    assert metrics.weight == 5.0


def test_http_error_is_wrapped() -> None:
    adapter = _adapter(httpx.MockTransport(lambda _: httpx.Response(503)))

    with pytest.raises(TransportCarbonException, match="Failed to calculate transport emissions"):
        adapter.calculate_emissions(TransportRequest("truck", 100.0, 5.0))


def test_malformed_response_is_wrapped_as_unexpected() -> None:
    adapter = _adapter(httpx.MockTransport(lambda _: httpx.Response(200, json={"oops": 1})))

    with pytest.raises(TransportCarbonException, match="Unexpected error"):
        adapter.calculate_emissions(TransportRequest("truck", 100.0, 5.0))
