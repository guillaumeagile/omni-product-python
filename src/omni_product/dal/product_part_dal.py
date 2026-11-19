"""Accès aux agrégats qui complètent un produit : un par contexte, reliés par `product_id`.

Ces fonctions ne connaissent que la clé du produit. Le service recompose la vue complète.
"""

from sqlalchemy.orm import Session

from omni_product.database import Base


def find[PartT: Base](session: Session, model: type[PartT], product_id: str) -> PartT | None:
    return session.get(model, product_id)


def save[PartT: Base](session: Session, part: PartT) -> PartT:
    return session.merge(part)


def delete[PartT: Base](session: Session, model: type[PartT], product_id: str) -> None:
    part = session.get(model, product_id)
    if part is not None:
        session.delete(part)
