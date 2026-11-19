from collections.abc import Iterable

from sqlalchemy.orm import Session

from omni_product.dal import product_dal
from omni_product.dal.product_dal import ProductContext
from omni_product.domain.model import Perishable, Product, ProductId
from omni_product.domain.model.freshness import is_expired


class ProductService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def find_all(self) -> list[Product]:
        return product_dal.find_all(self._session)

    def find_by_id(self, product_id: ProductId) -> Product | None:
        return product_dal.find_by_id(self._session, product_id)

    def find_context[T: ProductContext](self, context: type[T], product_id: ProductId) -> T:
        """Ce qu'un contexte (prix, stock, transport, fourniture) sait du produit."""
        return product_dal.context_of(self._session, context, product_id)

    def find_expired(self) -> list[Product]:
        """Les produits périssables dont la date d'expiration est passée."""
        return [product for product in self.find_all() if _is_past_its_date(product)]

    def save(self, product: Product) -> Product:
        return product_dal.save(self._session, product)

    def save_with_contexts(self, product: Product, contexts: Iterable[ProductContext]) -> Product:
        return product_dal.save_with_contexts(self._session, product, contexts)

    def delete_by_id(self, product_id: ProductId) -> None:
        product_dal.delete_by_id(self._session, product_id)


def _is_past_its_date(product: Product) -> bool:
    match product.shelf_life:
        case Perishable(expiration_date=date) if date is not None:
            return is_expired(date)
        case _:
            return False
