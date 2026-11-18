from __future__ import annotations

from dataclasses import dataclass

from result import Err, Ok, Result

from omni_product.domain.model.errors import ErreurFournisseur
from omni_product.domain.model.invariants import require_text
from omni_product.domain.model.product import ProductId
from omni_product.domain.model.supplier import Region, SupplierId


@dataclass(frozen=True)
class Siren:
    value: str

    @classmethod
    def of(cls, value: str) -> Result[Siren, ErreurFournisseur]:
        return require_text(cls, value, ErreurFournisseur).map(cls)


@dataclass(frozen=True)
class TvaId:
    value: str

    @classmethod
    def of(cls, value: str) -> Result[TvaId, ErreurFournisseur]:
        return require_text(cls, value, ErreurFournisseur).map(cls)


# Contexte Approvisionnement : qui fournit le produit, et les fournisseurs par région.
@dataclass(frozen=True)
class IdentifiantLegal:
    """Le SIREN et le numéro de TVA d'un fournisseur : tous deux, ou aucun."""

    siren: Siren
    tva_id: TvaId


@dataclass(frozen=True)
class RegionSupplier:
    """`Product.Supplier` en Java : fournisseur embarqué, par région."""

    name: str
    siren_tva: IdentifiantLegal | None = None


def region_supplier_of(
    name: str | None, siren: str | None, tva_id: str | None
) -> Result[RegionSupplier, ErreurFournisseur]:
    """Le fournisseur régional : un nom, et l'identifiant légal si le SIREN ou la TVA est donné."""
    if name is None:
        return Err(ErreurFournisseur("Un fournisseur régional a un nom"))
    if siren is None and tva_id is None:
        return Ok(RegionSupplier(name))
    if siren is None or tva_id is None:
        return Err(ErreurFournisseur("Le SIREN et le numéro de TVA vont ensemble"))
    return _avec_identifiant_legal(name, siren, tva_id)


def _avec_identifiant_legal(
    name: str, siren: str, tva_id: str
) -> Result[RegionSupplier, ErreurFournisseur]:
    match (Siren.of(siren), TvaId.of(tva_id)):
        case (Ok(numero), Ok(tva)):
            return Ok(RegionSupplier(name, IdentifiantLegal(numero, tva)))
        case (Err(erreur), _):
            return Err(erreur)
        case (_, Err(erreur)):
            return Err(erreur)


@dataclass(frozen=True)
class SupplierByRegion:
    region: Region
    supplier: RegionSupplier


@dataclass
class ProductSupply:
    """L'approvisionnement d'un produit, identifié par le produit lui-même."""

    id: ProductId
    supplier_id: SupplierId | None = None
    regions: tuple[SupplierByRegion, ...] = ()
