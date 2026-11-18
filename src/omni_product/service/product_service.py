from result import Result

from omni_product.domain.model import Product, ProductId, date_limite
from omni_product.domain.model.errors import InvalidValueError
from omni_product.domain.model.freshness import is_expired
from omni_product.domain.port.clock import Clock
from omni_product.domain.port.context_repository import ContextRepository


class ProductService:
    """Le cas d'usage du catalogue. Il ne connaît que le port des produits."""

    def __init__(self, products: ContextRepository[Product]) -> None:
        self._products = products

    def find_all(self) -> list[Product]:
        return self._products.find_all()

    def find_by_id(self, product_id: str) -> Result[Product | None, InvalidValueError]:
        return ProductId.of(product_id).map(self._products.find_by_id)

    def find_expired(self, clock: Clock) -> list[Product]:
        """Les produits périssables dont la date d'expiration est passée, à la date de `clock`."""
        return [
            product
            for product in self.find_all()
            if (limite := date_limite(product.shelf_life)) is not None and is_expired(limite, clock)
        ]

    def save(self, product: Product) -> Product:
        return self._products.save(product)

    def delete_by_id(self, product_id: str) -> Result[None, InvalidValueError]:
        return ProductId.of(product_id).map(self._products.delete_by_id)
