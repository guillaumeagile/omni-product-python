from sqlalchemy.orm import Session

from omni_product.anemic_model import ProductStock


def find_by_product_id(session: Session, product_id: str) -> ProductStock | None:
    return session.get(ProductStock, product_id)


def save(session: Session, stock: ProductStock) -> ProductStock:
    saved = session.merge(stock)
    session.commit()
    return saved
