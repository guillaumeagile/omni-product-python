from dataclasses import dataclass

from result import Err, Ok, Result

from omni_product.domain.model.errors import InvalidValueError
from omni_product.domain.model.transport import Distance, Kilos, TransportMode


@dataclass(frozen=True)
class TransportRequest:
    transport_mode: TransportMode
    distance_km: Distance
    weight_kg: Kilos

    @classmethod
    def of(
        cls, transport_mode: TransportMode, distance_km: Distance, weight_kg: Kilos
    ) -> Result["TransportRequest", InvalidValueError]:
        if distance_km.value <= 0:
            return Err(InvalidValueError("Distance must be positive"))
        if weight_kg.value <= 0:
            return Err(InvalidValueError("Weight must be positive"))
        return Ok(cls(transport_mode, distance_km, weight_kg))
