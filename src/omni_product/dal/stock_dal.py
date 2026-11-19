from sqlalchemy.orm import Session

from omni_product.dal.conversion import stock_from_row, stock_to_row
from omni_product.dal.rows import ProductStockRow
from omni_product.domain.model.stock import ProductStock


def find_by_product_id(session: Session, product_id: str) -> ProductStock | None:
    row = session.get(ProductStockRow, product_id)
    return None if row is None else stock_from_row(row)


def save(session: Session, stock: ProductStock) -> ProductStock:
    session.merge(stock_to_row(stock))
    session.commit()
    return stock
