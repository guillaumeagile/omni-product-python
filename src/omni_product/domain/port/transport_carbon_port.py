from typing import Protocol

from result import Result

from omni_product.domain.model.errors import ErreurTransport
from omni_product.domain.model.transport_carbon_metrics import TransportCarbonMetrics
from omni_product.domain.model.transport_request import TransportRequest


class TransportCarbonPort(Protocol):
    def calculate_emissions(
        self, transport_request: TransportRequest
    ) -> Result[TransportCarbonMetrics, ErreurTransport]: ...
