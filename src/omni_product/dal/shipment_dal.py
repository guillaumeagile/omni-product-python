from sqlalchemy.orm import Session

from omni_product.anemic_model import ProductShipment


def find_by_product_id(session: Session, product_id: str) -> ProductShipment | None:
    return session.get(ProductShipment, product_id)


def save(session: Session, shipment: ProductShipment) -> ProductShipment:
    saved = session.merge(shipment)
    session.commit()
    return saved
