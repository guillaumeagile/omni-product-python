"""Accès aux agrégats qui complètent un produit : un par contexte, reliés par `product_id`.

Ces fonctions ne connaissent que la clé du produit. Le service recompose la vue complète.
"""

from typing import TypeVar

from sqlalchemy.orm import Session

from omni_product.database import Base

PartT = TypeVar("PartT", bound=Base)


def find(session: Session, model: type[PartT], product_id: str) -> PartT | None:
    return session.get(model, product_id)


def save(session: Session, part: PartT) -> PartT:
    return session.merge(part)


def delete(session: Session, model: type[PartT], product_id: str) -> None:
    part = session.get(model, product_id)
    if part is not None:
        session.delete(part)
