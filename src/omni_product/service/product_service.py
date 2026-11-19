from sqlalchemy.orm import Session

from omni_product.anemic_model import PerishableProduct, Product, ProductAggregate
from omni_product.dal import product_dal
from omni_product.domain.model.freshness import is_expired


class ProductService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def find_all(self) -> list[ProductAggregate]:
        return product_dal.find_all(self._session)

    def find_by_id(self, product_id: str) -> ProductAggregate | None:
        return product_dal.find_by_id(self._session, product_id)

    def find_expired(self) -> list[Product]:
        """Les produits périssables dont la date d'expiration est passée."""
        return [
            aggregate.product
            for aggregate in self.find_all()
            if isinstance(aggregate.product, PerishableProduct)
            and aggregate.product.expiration_date is not None
            and is_expired(aggregate.product.expiration_date)
        ]

    def save(self, aggregate: ProductAggregate) -> ProductAggregate:
        return product_dal.save(self._session, aggregate)

    def delete_by_id(self, product_id: str) -> None:
        product_dal.delete_by_id(self._session, product_id)
