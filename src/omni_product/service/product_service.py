from sqlalchemy.orm import Session

from omni_product.dal import product_dal
from omni_product.dal.product_dal import ProductSheet


class ProductService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def find_all(self) -> list[ProductSheet]:
        return product_dal.find_all(self._session)

    def find_by_id(self, product_id: str) -> ProductSheet | None:
        return product_dal.find_by_id(self._session, product_id)

    def save(self, sheet: ProductSheet) -> ProductSheet:
        return product_dal.save(self._session, sheet)

    def delete_by_id(self, product_id: str) -> None:
        product_dal.delete_by_id(self._session, product_id)
