from sqlalchemy.orm import Session

from omni_product.anemic_model import (
    PerishableProduct,
    Product,
    ProductPrice,
    ProductShipment,
    ProductStock,
    ProductSupply,
)
from omni_product.dal import product_dal, product_part_dal
from omni_product.dal.product_part_dal import PartT
from omni_product.domain.model.freshness import is_expired
from omni_product.service.product_view import ProductView

# Les agrégats qui complètent un produit, un par contexte.
_PARTS = (ProductPrice, ProductShipment, ProductStock, ProductSupply)


class ProductService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def find_all(self) -> list[ProductView]:
        return [self._view_of(product) for product in product_dal.find_all(self._session)]

    def find_by_id(self, product_id: str) -> ProductView | None:
        product = product_dal.find_by_id(self._session, product_id)
        return None if product is None else self._view_of(product)

    def find_expired(self) -> list[ProductView]:
        """Les produits périssables dont la date d'expiration est passée."""
        return [
            view
            for view in self.find_all()
            if isinstance(view.product, PerishableProduct)
            and view.product.expiration_date is not None
            and is_expired(view.product.expiration_date)
        ]

    def save(self, view: ProductView) -> ProductView:
        """Enregistre le produit et ses agrégats dans une seule transaction."""
        saved = ProductView(
            product=product_dal.save(self._session, view.product),
            price=_save_part(self._session, view.price),
            shipment=_save_part(self._session, view.shipment),
            stock=_save_part(self._session, view.stock),
            supply=_save_part(self._session, view.supply),
        )
        self._session.commit()
        return saved

    def delete_by_id(self, product_id: str) -> None:
        for model in _PARTS:
            product_part_dal.delete(self._session, model, product_id)
        product = product_dal.find_by_id(self._session, product_id)
        if product is not None:
            product_dal.delete(self._session, product)
        self._session.commit()

    def _view_of(self, product: Product) -> ProductView:
        return ProductView(
            product=product,
            price=product_part_dal.find(self._session, ProductPrice, product.id),
            shipment=product_part_dal.find(self._session, ProductShipment, product.id),
            stock=product_part_dal.find(self._session, ProductStock, product.id),
            supply=product_part_dal.find(self._session, ProductSupply, product.id),
        )


def _save_part(session: Session, part: PartT | None) -> PartT | None:
    return None if part is None else product_part_dal.save(session, part)
