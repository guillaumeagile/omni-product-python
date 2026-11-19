from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from omni_product.dal.conversion import price_from_row, price_to_row
from omni_product.dal.rows import ProductDiscountRow, ProductPriceRow
from omni_product.domain.model.pricing import ProductPrice


def find_price(session: Session, product_id: str) -> ProductPrice | None:
    row = session.get(ProductPriceRow, product_id)
    return None if row is None else price_from_row(row)


def save_price(session: Session, price: ProductPrice) -> ProductPrice:
    session.merge(price_to_row(price))
    session.commit()
    return price


def find_discounts(session: Session, product_id: str) -> list[str]:
    statement = (
        select(ProductDiscountRow.discount)
        .where(ProductDiscountRow.product_id == product_id)
        .order_by(ProductDiscountRow.id)
    )
    return list(session.scalars(statement))


def replace_discounts(session: Session, product_id: str, discounts: list[str]) -> None:
    """Remplace la liste des remises du produit (comme `PUT` en Java)."""
    session.execute(delete(ProductDiscountRow).where(ProductDiscountRow.product_id == product_id))
    session.add_all(
        [ProductDiscountRow(product_id=product_id, discount=discount) for discount in discounts]
    )
    session.commit()
