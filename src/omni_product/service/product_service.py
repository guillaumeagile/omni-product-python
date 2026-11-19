from sqlalchemy.orm import Session

from omni_product.anemic_model import (
    PerishableProduct,
    Product,
    ProductPricing,
    ProductStorage,
    ProductSupply,
    ProductTransport,
)
from omni_product.dal import product_dal
from omni_product.domain.model.freshness import is_expired
from omni_product.service.product_sheet import ProductSheet


class ProductService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def find_all(self) -> list[Product]:
        return product_dal.find_all(self._session)

    def find_by_id(self, product_id: str) -> Product | None:
        return product_dal.find_by_id(self._session, product_id)

    def find_all_sheets(self) -> list[ProductSheet]:
        return [self._sheet_of(product) for product in self.find_all()]

    def find_sheet(self, product_id: str) -> ProductSheet | None:
        product = self.find_by_id(product_id)
        return self._sheet_of(product) if product is not None else None

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

    def save_sheet(self, sheet: ProductSheet) -> ProductSheet:
        saved = product_dal.save_with_contexts(
            self._session,
            sheet.product,
            [sheet.pricing, sheet.storage, sheet.transport, sheet.supply],
        )
        return self._sheet_of(saved)

    def delete_by_id(self, product_id: str) -> None:
        product_dal.delete_by_id(self._session, product_id)

    def _sheet_of(self, product: Product) -> ProductSheet:
        return ProductSheet(
            product=product,
            pricing=product_dal.context_of(self._session, ProductPricing, product.id),
            storage=product_dal.context_of(self._session, ProductStorage, product.id),
            transport=product_dal.context_of(self._session, ProductTransport, product.id),
            supply=product_dal.context_of(self._session, ProductSupply, product.id),
        )
