import pytest

from omni_product.domain.model.transport import CarbonKilos, Distance, Kilos, TransportMode
from omni_product.domain.model.transport_carbon_metrics import TransportCarbonMetrics
from omni_product.domain.model.transport_request import TransportRequest


def test_valid_request() -> None:
    request = TransportRequest(TransportMode.parse("truck"), Distance(120.0), Kilos(3.5))

    assert request.transport_mode == TransportMode("truck")


def test_transport_mode_accepts_only_the_closed_list() -> None:
    assert TransportMode.parse("train") == TransportMode("train")

    with pytest.raises(ValueError, match="TransportMode doit être"):
        TransportMode.parse("bicycle")


@pytest.mark.parametrize(
    ("mode", "distance", "weight", "message"),
    [
        ("", 1.0, 1.0, "TransportMode doit être"),
        ("truck", 0.0, 1.0, "Distance must be positive"),
        ("truck", 1.0, 0.0, "Weight must be positive"),
    ],
)
def test_invalid_request(mode: str, distance: float, weight: float, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        TransportRequest(TransportMode.parse(mode), Distance(distance), Kilos(weight))


def test_negative_measures_are_rejected() -> None:
    with pytest.raises(ValueError, match="Distance cannot be negative"):
        Distance(-1.0)
    with pytest.raises(ValueError, match="Kilos cannot be negative"):
        Kilos(-1.0)


def test_negative_carbon_metrics_are_rejected() -> None:
    with pytest.raises(ValueError, match="cannot be negative"):
        CarbonKilos(-1.0)
    with pytest.raises(ValueError, match="cannot be negative"):
        TransportCarbonMetrics(
            CarbonKilos(-1.0),
            None,
            TransportMode("truck"),
            Distance(10.0),
            Kilos(1.0),
        )
