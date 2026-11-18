from result import Ok

from omni_product.domain.model.procurement import (
    IdentifiantLegal,
    RegionSupplier,
    Siren,
    TvaId,
    region_supplier_of,
)

MSG_NOM = "Un fournisseur régional a un nom"
MSG_SIREN_ET_TVA = "Le SIREN et le numéro de TVA vont ensemble"


def test_regional_supplier_needs_a_name() -> None:
    assert str(region_supplier_of(None, None, None).unwrap_err()) == MSG_NOM


def test_regional_supplier_without_legal_identifier() -> None:
    assert region_supplier_of("Nord", None, None) == Ok(RegionSupplier("Nord"))


def test_regional_supplier_with_legal_identifier() -> None:
    assert region_supplier_of("Nord", "123456789", "FR12345") == Ok(
        RegionSupplier("Nord", IdentifiantLegal(Siren("123456789"), TvaId("FR12345")))
    )


def test_siren_and_tva_go_together() -> None:
    assert str(region_supplier_of("Nord", "123456789", None).unwrap_err()) == MSG_SIREN_ET_TVA
    assert str(region_supplier_of("Nord", None, "FR12345").unwrap_err()) == MSG_SIREN_ET_TVA


def test_empty_siren_is_refused_with_the_siren_error() -> None:
    erreur_attendue = str(Siren.of("").unwrap_err())

    assert str(region_supplier_of("Nord", "", "FR12345").unwrap_err()) == erreur_attendue


def test_empty_tva_is_refused_with_the_tva_error() -> None:
    erreur_attendue = str(TvaId.of("").unwrap_err())

    assert str(region_supplier_of("Nord", "123456789", "").unwrap_err()) == erreur_attendue
