"""Les identifiants partagés par tous les contextes : le noyau ne dépend de rien d'autre.

Les ports et le domaine importent leurs identifiants d'ici. Un identifiant ne contient aucune
règle métier au-delà de sa forme.
"""

from __future__ import annotations

from dataclasses import dataclass

from result import Result

from omni_product.kernel.errors import ErreurFournisseur, ErreurProduit
from omni_product.kernel.invariants import require_text


@dataclass(frozen=True)
class ProductId:
    value: str

    @classmethod
    def of(cls, value: str) -> Result[ProductId, ErreurProduit]:
        return require_text(cls, value, ErreurProduit).map(cls)


@dataclass(frozen=True)
class SupplierId:
    value: str

    @classmethod
    def of(cls, value: str) -> Result[SupplierId, ErreurFournisseur]:
        return require_text(cls, value, ErreurFournisseur).map(cls)
