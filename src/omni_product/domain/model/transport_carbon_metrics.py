from dataclasses import dataclass

from omni_product.domain.model.transport import CarbonEmission, Distance, TransportMode, Weight


@dataclass(frozen=True)
class TransportCarbonMetrics:
    """Les valeurs négatives sont refusées par chaque Value Object."""

    co2_equivalent_kg: CarbonEmission
    co2_direct_kg: CarbonEmission | None
    transport_mode: TransportMode
    distance: Distance
    weight: Weight
