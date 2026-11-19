from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from omni_product.anemic_model import PerishableProduct, Price, Product, RegionSupplier, Warehouse
from omni_product.dal import pricing_dal, product_dal, storage_dal, supplier_dal, transport_dal
from omni_product.domain.model.freshness import is_expired


@dataclass
class ProductDetails:
    """Ce que les autres contextes savent d'un produit, rassemblé pour l'écriture ou la lecture.

    `price` et `warehouse` à None signifient « non fourni » : la valeur en place est alors gardée.
    """

    price: Price | None = None
    discounts: list[str] = field(default_factory=list[str])
    images: dict[str, str | None] = field(default_factory=dict[str, str | None])
    suppliers_regions: dict[str, RegionSupplier] = field(default_factory=dict[str, RegionSupplier])
    kilos: float | None = None
    volume: str | None = None
    quantity: int | None = None
    stock: int | None = None
    warehouse: Warehouse | None = None


class ProductService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def find_all(self) -> list[Product]:
        return product_dal.find_all(self._session)

    def find_by_id(self, product_id: str) -> Product | None:
        return product_dal.find_by_id(self._session, product_id)

    def details_of(self, product_id: str) -> ProductDetails:
        session = self._session
        stock_row = storage_dal.find(session, product_id)
        transport_row = transport_dal.find(session, product_id)
        return ProductDetails(
            price=pricing_dal.find_price(session, product_id) or Price(),
            discounts=pricing_dal.find_discounts(session, product_id),
            images=product_dal.find_images(session, product_id),
            suppliers_regions=supplier_dal.find_regions(session, product_id),
            kilos=transport_row.kilos if transport_row is not None else None,
            volume=transport_row.volume if transport_row is not None else None,
            quantity=stock_row.quantity if stock_row is not None else None,
            stock=stock_row.stock if stock_row is not None else None,
            warehouse=stock_row.warehouse if stock_row is not None else None,
        )

    def find_expired(self) -> list[Product]:
        """Les produits périssables dont la date d'expiration est passée."""
        return [
            product
            for product in self.find_all()
            if isinstance(product, PerishableProduct)
            and product.expiration_date is not None
            and is_expired(product.expiration_date)
        ]

    def save(self, product: Product, details: ProductDetails | None = None) -> Product:
        details = details or ProductDetails()
        saved = product_dal.merge(self._session, product)
        product_dal.replace_images(self._session, saved.id, details.images)
        pricing_dal.replace(self._session, saved.id, details.price, details.discounts)
        transport_dal.replace(self._session, saved.id, details.kilos, details.volume)
        storage_dal.replace(
            self._session, saved.id, details.quantity, details.stock, details.warehouse
        )
        supplier_dal.replace_regions(self._session, saved.id, details.suppliers_regions)
        self._session.commit()
        return saved

    def delete_by_id(self, product_id: str) -> None:
        product_dal.delete_by_id(self._session, product_id)

    def delete_by_supplier_id(self, supplier_id: str) -> None:
        product_dal.delete_by_supplier_id(self._session, supplier_id)
