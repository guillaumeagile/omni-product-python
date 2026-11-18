from result import Result

from omni_product.domain.model import ProductId, date_limite
from omni_product.domain.model.errors import InvalidValueError
from omni_product.domain.model.freshness import is_expired
from omni_product.domain.model.product_sheet import ProductSheet
from omni_product.domain.port.clock import Clock
from omni_product.domain.port.product_repository import ProductRepository


class ProductService:
    """Le cas d'usage du catalogue. Il ne connaît que le port `ProductRepository`."""

    def __init__(self, products: ProductRepository) -> None:
        self._products = products

    def find_all(self) -> list[ProductSheet]:
        return self._products.find_all()

    def find_by_id(self, product_id: str) -> Result[ProductSheet | None, InvalidValueError]:
        return ProductId.of(product_id).map(self._products.find_by_id)

    def find_expired(self, clock: Clock) -> list[ProductSheet]:
        """Les produits périssables dont la date d'expiration est passée, à la date de `clock`."""
        return [
            sheet
            for sheet in self.find_all()
            if (limite := date_limite(sheet.product.shelf_life)) is not None
            and is_expired(limite, clock)
        ]

    def save(self, sheet: ProductSheet) -> ProductSheet:
        return self._products.save(sheet)

    def delete_by_id(self, product_id: str) -> Result[None, InvalidValueError]:
        return ProductId.of(product_id).map(self._products.delete_by_id)
