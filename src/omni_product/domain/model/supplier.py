from __future__ import annotations

from dataclasses import dataclass

from result import Result

from omni_product.domain.model.errors import ErreurFournisseur
from omni_product.domain.model.invariants import require_text

# Contexte Approvisionnement : le fournisseur lui-même. Les produits qu'il fournit sont liés
# par `ProductSupply`, dans `procurement.py`.


@dataclass(frozen=True)
class SupplierId:
    value: str

    @classmethod
    def of(cls, value: str) -> Result[SupplierId, ErreurFournisseur]:
        return require_text(cls, value, ErreurFournisseur).map(cls)


@dataclass(frozen=True)
class Region:
    value: str

    @classmethod
    def of(cls, value: str) -> Result[Region, ErreurFournisseur]:
        return require_text(cls, value, ErreurFournisseur).map(cls)


@dataclass
class Supplier:
    id: SupplierId
    name: str
