"""Supplier : qui fournit le produit, globalement et par région."""

from dataclasses import dataclass, field

from omni_product.domain.exception.invalid_value import InvalidValue
from omni_product.domain.model.identity import ProductId, SupplierId


@dataclass(frozen=True)
class Siren:
    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise InvalidValue("Siren is required")


@dataclass(frozen=True)
class TvaId:
    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise InvalidValue("TVA id is required")


@dataclass(frozen=True)
class RegionSupplier:
    """`Product.Supplier` en Java : fournisseur embarqué, par région."""

    name: str | None = None
    siren: Siren | None = None
    tva_id: TvaId | None = None


@dataclass(eq=False)
class ProductSupply:
    """Le produit vu du Supplier : il partage l'identité du produit."""

    id: ProductId
    supplier_id: SupplierId | None = None
    suppliers_regions: dict[str, RegionSupplier] = field(default_factory=dict[str, RegionSupplier])
