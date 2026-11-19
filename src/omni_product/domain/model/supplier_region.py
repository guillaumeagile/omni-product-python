from dataclasses import dataclass


@dataclass
class RegionSupplier:
    """`Product.Supplier` en Java : fournisseur embarqué, par région."""

    name: str | None = None
    siren: str | None = None
    tva_id: str | None = None
