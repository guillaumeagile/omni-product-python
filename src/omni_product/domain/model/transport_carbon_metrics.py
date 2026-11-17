from dataclasses import dataclass

from omni_product.domain.model.transport import CarbonKilos, Distance, Kilos, TransportMode


@dataclass(frozen=True)
class TransportCarbonMetrics:
    co2_equivalent_kg: CarbonKilos
    co2_direct_kg: CarbonKilos | None
    transport_mode: TransportMode
    distance: Distance
    weight: Kilos
