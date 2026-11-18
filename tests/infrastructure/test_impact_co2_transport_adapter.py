import json

import httpx

from omni_product.domain.model.transport import CarbonKilos, Distance, Kilos, TransportMode
from omni_product.domain.model.transport_request import TransportRequest
from omni_product.infrastructure.adapter.impact_co2_api_client import ImpactCo2ApiClient
from omni_product.infrastructure.adapter.impact_co2_transport_adapter import (
    ImpactCo2TransportAdapter,
)

BASE_URL = "https://impactco2.test/api/v1"


def _adapter(handler: httpx.MockTransport) -> ImpactCo2TransportAdapter:
    client = ImpactCo2ApiClient(httpx.Client(transport=handler), BASE_URL)
    return ImpactCo2TransportAdapter(client)


def _request() -> TransportRequest:
    return TransportRequest(TransportMode("truck"), Distance(100.0), Kilos(5.0))


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

    metrics = _adapter(httpx.MockTransport(handle)).calculate_emissions(_request()).unwrap()

    assert seen["url"] == f"{BASE_URL}/transport/emissions"
    assert seen["body"] == {"transport_mode": "truck", "distance_km": 100.0, "weight_kg": 5.0}
    assert metrics.co2_equivalent_kg == CarbonKilos(4.2)
    assert metrics.co2_direct_kg == CarbonKilos(3.9)
    assert metrics.transport_mode == TransportMode("truck")
    assert metrics.distance.value == 100.0
    assert metrics.weight.value == 5.0


def test_http_error_is_returned_as_a_value() -> None:
    adapter = _adapter(httpx.MockTransport(lambda _: httpx.Response(503)))

    result = adapter.calculate_emissions(_request())

    assert result.is_err()
    assert str(result.unwrap_err()).startswith("Failed to calculate transport emissions")


def test_malformed_response_is_returned_as_an_unexpected_error() -> None:
    adapter = _adapter(httpx.MockTransport(lambda _: httpx.Response(200, json={"oops": 1})))

    result = adapter.calculate_emissions(_request())

    assert result.is_err()
    assert str(result.unwrap_err()).startswith("Unexpected error")


def test_response_with_a_mode_outside_the_closed_list_is_an_unexpected_error() -> None:
    body = {
        "co2_equivalent_kg": 4.2,
        "co2_direct_kg": None,
        "transport_mode": "boat",
        "distance_km": 100.0,
        "weight_kg": 5.0,
    }
    adapter = _adapter(httpx.MockTransport(lambda _: httpx.Response(200, json=body)))

    result = adapter.calculate_emissions(_request())

    assert result.is_err()
    assert str(result.unwrap_err()).startswith("Unexpected error")
