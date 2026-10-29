from sqlalchemy import select
from sqlalchemy.orm import Session

from omni_product.model import Product


class ProductRepository:
    """Équivalent de `JpaRepository<Product, String>` : chaque opération d'écriture est validée."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def find_all(self) -> list[Product]:
        return list(self._session.scalars(select(Product).order_by(Product.id)))

    def find_by_id(self, product_id: str) -> Product | None:
        return self._session.get(Product, product_id)

    def find_by_slug(self, slug: str) -> Product | None:
        return self._session.scalars(select(Product).where(Product.slug == slug)).first()

    def exists_by_slug(self, slug: str) -> bool:
        return self.find_by_slug(slug) is not None

    def save(self, product: Product) -> Product:
        saved = self._session.merge(product)
        self._session.commit()
        return saved

    def delete_by_id(self, product_id: str) -> None:
        product = self.find_by_id(product_id)
        if product is not None:
            self._session.delete(product)
            self._session.commit()

    def delete_by_slug(self, slug: str) -> None:
        product = self.find_by_slug(slug)
        if product is not None:
            self._session.delete(product)
            self._session.commit()

    def delete_all(self) -> None:
        for product in self.find_all():
            self._session.delete(product)
        self._session.commit()
