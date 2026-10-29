from sqlalchemy import select
from sqlalchemy.orm import Session

from omni_product.model import Product, Supplier


class SupplierRepository:
    """Équivalent de `JpaRepository<Supplier, String>`."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def find_all(self) -> list[Supplier]:
        return list(self._session.scalars(select(Supplier).order_by(Supplier.id)))

    def find_by_id(self, supplier_id: str) -> Supplier | None:
        return self._session.get(Supplier, supplier_id)

    def find_by_country(self, country: str) -> list[Supplier]:
        return self._find_all_where(Supplier.country == country)

    def find_by_region(self, region: str) -> list[Supplier]:
        return self._find_all_where(Supplier.region == region)

    def find_by_name(self, name: str) -> Supplier | None:
        return self._session.scalars(select(Supplier).where(Supplier.name == name)).first()

    def find_by_product_id(self, product_id: str) -> list[Supplier]:
        """Requête SQL à la place du filtrage en mémoire qui causait le lazy loading Java."""
        return self._find_all_where(Supplier.products.any(Product.id == product_id))

    def save(self, supplier: Supplier) -> Supplier:
        saved = self._session.merge(supplier)
        self._session.commit()
        return saved

    def delete(self, supplier: Supplier) -> None:
        self._session.delete(supplier)
        self._session.commit()

    def delete_all(self) -> None:
        for supplier in self.find_all():
            self._session.delete(supplier)
        self._session.commit()

    def _find_all_where(self, criterion: object) -> list[Supplier]:
        statement = select(Supplier).where(criterion).order_by(Supplier.id)  # pyright: ignore[reportArgumentType]
        return list(self._session.scalars(statement))
