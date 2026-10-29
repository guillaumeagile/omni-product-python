from typing import Protocol

from omni_product.domain.model.transport_carbon_metrics import TransportCarbonMetrics
from omni_product.domain.model.transport_request import TransportRequest


class TransportCarbonPort(Protocol):
    def calculate_emissions(
        self, transport_request: TransportRequest
    ) -> TransportCarbonMetrics: ...
