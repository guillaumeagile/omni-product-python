from dataclasses import dataclass


@dataclass(frozen=True)
class Siren:
    value: str


@dataclass(frozen=True)
class TvaId:
    value: str


@dataclass(frozen=True)
class RegionSupplier:
    """`Product.Supplier` en Java : fournisseur embarqué, par région."""

    name: str | None = None
    siren: Siren | None = None
    tva_id: TvaId | None = None
