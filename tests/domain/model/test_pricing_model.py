from result import Err, Ok

from omni_product.domain.model.errors import ErreurTarification
from omni_product.domain.model.pricing import Amount, PrixAvecTaxe, PrixHorsTaxe, Rate, prix_of

MSG_TAXE_SANS_BASE = "Une taxe demande un prix de base"
MSG_TAXE_MONTANT_ET_TAUX = "Une taxe demande son montant et son taux"


def test_no_price_when_no_value_is_given() -> None:
    assert prix_of(None, None, None) == Ok(None)


def test_tax_without_base_price_is_refused() -> None:
    assert str(prix_of(None, 2.0, None).unwrap_err()) == MSG_TAXE_SANS_BASE
    assert str(prix_of(None, None, 0.2).unwrap_err()) == MSG_TAXE_SANS_BASE
    assert str(prix_of(None, 2.0, 0.2).unwrap_err()) == MSG_TAXE_SANS_BASE


def test_base_price_without_tax_is_a_price_without_tax() -> None:
    assert prix_of(10.0, None, None) == Ok(PrixHorsTaxe(Amount(10.0)))


def test_base_price_with_tax_and_rate_is_a_price_with_tax() -> None:
    assert prix_of(10.0, 2.0, 0.2) == Ok(PrixAvecTaxe(Amount(10.0), Amount(2.0), Rate(0.2)))


def test_tax_needs_both_amount_and_rate() -> None:
    assert str(prix_of(10.0, 2.0, None).unwrap_err()) == MSG_TAXE_MONTANT_ET_TAUX
    assert str(prix_of(10.0, None, 0.2).unwrap_err()) == MSG_TAXE_MONTANT_ET_TAUX


def test_negative_base_price_is_refused() -> None:
    assert isinstance(prix_of(-1.0, None, None).unwrap_err(), ErreurTarification)


def test_negative_tax_amount_is_refused() -> None:
    assert isinstance(prix_of(10.0, -1.0, 0.2).unwrap_err(), ErreurTarification)


def test_tax_rate_out_of_range_is_refused() -> None:
    assert isinstance(prix_of(10.0, 2.0, 1.5).unwrap_err(), ErreurTarification)


def test_invalid_tax_rate_is_refused_when_tax_amount_is_valid() -> None:
    assert isinstance(prix_of(10.0, 2.0, -0.1), Err)


def test_invalid_tax_amount_is_refused_when_rate_is_valid() -> None:
    assert isinstance(prix_of(10.0, -2.0, 0.2), Err)
