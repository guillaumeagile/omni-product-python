from sqlalchemy.orm import Session

from omni_product.dal import product_dal
from omni_product.model import Product


class ProductService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def find_all(self) -> list[Product]:
        return product_dal.find_all(self._session)

    def find_by_id(self, product_id: str) -> Product | None:
        return product_dal.find_by_id(self._session, product_id)

    def save(self, product: Product) -> Product:
        return product_dal.save(self._session, product)

    def delete_by_id(self, product_id: str) -> None:
        product_dal.delete_by_id(self._session, product_id)
