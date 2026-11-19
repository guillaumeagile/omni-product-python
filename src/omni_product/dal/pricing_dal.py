from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from omni_product.anemic_model import ProductDiscount, ProductPrice


def find_price(session: Session, product_id: str) -> ProductPrice | None:
    return session.get(ProductPrice, product_id)


def save_price(session: Session, price: ProductPrice) -> ProductPrice:
    saved = session.merge(price)
    session.commit()
    return saved


def find_discounts(session: Session, product_id: str) -> list[str]:
    statement = (
        select(ProductDiscount.discount)
        .where(ProductDiscount.product_id == product_id)
        .order_by(ProductDiscount.id)
    )
    return list(session.scalars(statement))


def replace_discounts(session: Session, product_id: str, discounts: list[str]) -> None:
    """Remplace la liste des remises du produit (comme `PUT` en Java)."""
    session.execute(delete(ProductDiscount).where(ProductDiscount.product_id == product_id))
    session.add_all([ProductDiscount(product_id, discount) for discount in discounts])
    session.commit()
