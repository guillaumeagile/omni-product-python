from omni_product.model import Product
from omni_product.repository.product_repository import ProductRepository


class ProductService:
    def __init__(self, product_repository: ProductRepository) -> None:
        self._product_repository = product_repository

    def find_all(self) -> list[Product]:
        return self._product_repository.find_all()

    def find_by_id(self, product_id: str) -> Product | None:
        return self._product_repository.find_by_id(product_id)

    def save(self, product: Product) -> Product:
        return self._product_repository.save(product)

    def delete_by_id(self, product_id: str) -> None:
        self._product_repository.delete_by_id(product_id)
