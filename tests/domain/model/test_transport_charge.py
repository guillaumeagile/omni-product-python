from result import Ok

from omni_product.domain.model.transport import Charge, Kilos, Volume, charge_of

MSG_POIDS_ET_VOLUME = "Le poids et le volume vont ensemble"


def test_no_charge_when_neither_weight_nor_volume_is_given() -> None:
    assert charge_of(None, None) == Ok(None)


def test_weight_and_volume_make_a_charge() -> None:
    assert charge_of(2.5, "0.5 m3") == Ok(Charge(Kilos(2.5), Volume("0.5 m3")))


def test_weight_and_volume_go_together() -> None:
    assert str(charge_of(2.5, None).unwrap_err()) == MSG_POIDS_ET_VOLUME
    assert str(charge_of(None, "0.5 m3").unwrap_err()) == MSG_POIDS_ET_VOLUME


def test_negative_weight_is_refused_with_the_weight_error() -> None:
    erreur_attendue = str(Kilos.of(-1.0).unwrap_err())

    assert str(charge_of(-1.0, "0.5 m3").unwrap_err()) == erreur_attendue


def test_empty_volume_is_refused_with_the_volume_error() -> None:
    erreur_attendue = str(Volume.of("").unwrap_err())

    assert str(charge_of(2.5, "").unwrap_err()) == erreur_attendue
