from sqlalchemy.orm import Session

from omni_product.dal.conversion import shipment_from_row, shipment_to_row
from omni_product.dal.rows import ProductShipmentRow
from omni_product.domain.model.shipment import ProductShipment


def find_by_product_id(session: Session, product_id: str) -> ProductShipment | None:
    row = session.get(ProductShipmentRow, product_id)
    return None if row is None else shipment_from_row(row)


def save(session: Session, shipment: ProductShipment) -> ProductShipment:
    session.merge(shipment_to_row(shipment))
    session.commit()
    return shipment
