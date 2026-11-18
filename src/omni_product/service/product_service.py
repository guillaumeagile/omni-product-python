from result import Result
from sqlalchemy.orm import Session

from omni_product.dal import product_dal
from omni_product.dal.product_dal import ProductSheet
from omni_product.domain.model import Perishable, ProductId
from omni_product.domain.model.errors import InvalidValueError
from omni_product.domain.model.freshness import is_expired
from omni_product.domain.port.clock import Clock


class ProductService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def find_all(self) -> list[ProductSheet]:
        return product_dal.find_all(self._session)

    def find_by_id(self, product_id: str) -> Result[ProductSheet | None, InvalidValueError]:
        return ProductId.of(product_id).map(self._find_by_id)

    def find_expired(self, clock: Clock) -> list[ProductSheet]:
        """Les produits périssables dont la date d'expiration est passée, à la date de `clock`."""
        return [
            sheet
            for sheet in self.find_all()
            if isinstance(sheet.product.shelf_life, Perishable)
            and sheet.product.shelf_life.expiration_date is not None
            and is_expired(sheet.product.shelf_life.expiration_date, clock)
        ]

    def save(self, sheet: ProductSheet) -> ProductSheet:
        return product_dal.save(self._session, sheet)

    def delete_by_id(self, product_id: str) -> Result[None, InvalidValueError]:
        return ProductId.of(product_id).map(self._delete_by_id)

    def _find_by_id(self, product_id: ProductId) -> ProductSheet | None:
        return product_dal.find_by_id(self._session, product_id)

    def _delete_by_id(self, product_id: ProductId) -> None:
        product_dal.delete_by_id(self._session, product_id)
