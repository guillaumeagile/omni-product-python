from sqlalchemy.orm import Session

from omni_product.anemic_model import PerishableProduct, Product, ProductShipment, ProductStock
from omni_product.dal import product_dal, shipment_dal, stock_dal
from omni_product.domain.model.freshness import is_expired


class ProductService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def find_all(self) -> list[Product]:
        return product_dal.find_all(self._session)

    def find_by_id(self, product_id: str) -> Product | None:
        return product_dal.find_by_id(self._session, product_id)

    def find_expired(self) -> list[Product]:
        """Les produits périssables dont la date d'expiration est passée."""
        return [
            product
            for product in self.find_all()
            if isinstance(product, PerishableProduct)
            and product.expiration_date is not None
            and is_expired(product.expiration_date)
        ]

    def save(self, product: Product) -> Product:
        return product_dal.save(self._session, product)

    def find_stock(self, product_id: str) -> ProductStock | None:
        return stock_dal.find_by_product_id(self._session, product_id)

    def save_stock(self, stock: ProductStock) -> ProductStock:
        return stock_dal.save(self._session, stock)

    def find_shipment(self, product_id: str) -> ProductShipment | None:
        return shipment_dal.find_by_product_id(self._session, product_id)

    def save_shipment(self, shipment: ProductShipment) -> ProductShipment:
        return shipment_dal.save(self._session, shipment)

    def delete_by_id(self, product_id: str) -> None:
        product_dal.delete_by_id(self._session, product_id)
