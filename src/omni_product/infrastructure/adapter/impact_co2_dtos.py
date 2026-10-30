from pydantic import BaseModel


class ImpactCo2Request(BaseModel):
    transport_mode: str
    distance_km: float
    weight_kg: float


class ImpactCo2Response(ImpactCo2Request):
    """Hérite des trois champs de transport de la requête, par commodité."""

    co2_equivalent_kg: float
    co2_direct_kg: float | None = None
