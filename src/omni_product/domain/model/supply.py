"""Supplier : qui fournit le produit, globalement et par région."""

from dataclasses import dataclass, field


@dataclass
class RegionSupplier:
    """`Product.Supplier` en Java : fournisseur embarqué, par région."""

    name: str | None = None
    siren: str | None = None
    tva_id: str | None = None


@dataclass(eq=False)
class ProductSupply:
    product_id: str
    supplier_id: str | None = None
    suppliers_regions: dict[str, RegionSupplier] = field(default_factory=dict[str, RegionSupplier])
