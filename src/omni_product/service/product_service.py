from sqlalchemy.orm import Session

from omni_product.anemic_model import (
    PerishableProduct,
    Product,
    ProductPricing,
    ProductStorage,
    ProductSupplierContext,
    ProductTransport,
)
from omni_product.dal import product_dal
from omni_product.domain.model.freshness import is_expired

type ProductRecord = tuple[
    Product,
    ProductPricing | None,
    ProductStorage | None,
    ProductTransport | None,
    ProductSupplierContext | None,
]


class ProductService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def find_all(self) -> list[ProductRecord]:
        return product_dal.find_all_records(self._session)

    def find_by_id(self, product_id: str) -> ProductRecord | None:
        return product_dal.find_record_by_id(self._session, product_id)

    def find_expired(self) -> list[Product]:
        """Les produits périssables dont la date d'expiration est passée."""
        return [
            product
            for product in product_dal.find_all(self._session)
            if isinstance(product, PerishableProduct)
            and product.expiration_date is not None
            and is_expired(product.expiration_date)
        ]

    def save(self, product: Product) -> Product:
        return product_dal.save(self._session, product)

    def save_record(self, record: ProductRecord) -> ProductRecord:
        return product_dal.save_record(self._session, record)

    def delete_by_id(self, product_id: str) -> None:
        product_dal.delete_by_id(self._session, product_id)
