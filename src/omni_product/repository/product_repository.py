from sqlalchemy import select

from omni_product.model import Product
from omni_product.repository.session_repository import SessionRepository


class ProductRepository(SessionRepository):
    """Équivalent de `JpaRepository<Product, String>` : chaque opération d'écriture est validée."""

    def find_all(self) -> list[Product]:
        return list(self._session.scalars(select(Product).order_by(Product.id)))

    def find_by_id(self, product_id: str) -> Product | None:
        return self._session.get(Product, product_id)

    def find_by_slug(self, slug: str) -> Product | None:
        return self._session.scalars(select(Product).where(Product.slug == slug)).first()

    def exists_by_slug(self, slug: str) -> bool:
        return self.find_by_slug(slug) is not None

    def save(self, product: Product) -> Product:
        return self._merge_and_commit(product)

    def delete_by_id(self, product_id: str) -> None:
        product = self.find_by_id(product_id)
        if product is not None:
            self._delete_and_commit(product)

    def delete_by_slug(self, slug: str) -> None:
        product = self.find_by_slug(slug)
        if product is not None:
            self._delete_and_commit(product)

    def delete_all(self) -> None:
        for product in self.find_all():
            self._session.delete(product)
        self._session.commit()
