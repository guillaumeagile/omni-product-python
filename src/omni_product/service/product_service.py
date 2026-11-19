from sqlalchemy.orm import Session

from omni_product.anemic_model import PerishableProduct, Product, ProductTransport
from omni_product.dal import product_dal, product_transport_dal
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

    def find_transport(self, product_id: str) -> ProductTransport | None:
        return product_transport_dal.find_by_product_id(self._session, product_id)

    def save(self, product: Product, transport: ProductTransport | None = None) -> Product:
        saved = product_dal.save(self._session, product)
        if transport is not None:
            product_transport_dal.save(self._session, transport)
        return saved

    def delete_by_id(self, product_id: str) -> None:
        product_transport_dal.delete_by_product_id(self._session, product_id)
        product_dal.delete_by_id(self._session, product_id)
