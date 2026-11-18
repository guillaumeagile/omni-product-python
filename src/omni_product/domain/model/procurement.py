from __future__ import annotations

from dataclasses import dataclass

from result import Result

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
class RegionSupplier:
    """`Product.Supplier` en Java : fournisseur embarqué, par région."""

    name: str | None = None
    siren: Siren | None = None
    tva_id: TvaId | None = None


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
