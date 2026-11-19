from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.orm import Mapped, composite, mapped_column, relationship
from sqlalchemy.orm.collections import attribute_keyed_dict

from omni_product.anemic_model.catalog import ProductImage
from omni_product.anemic_model.pricing import Price, ProductDiscount
from omni_product.anemic_model.storage import Warehouse
from omni_product.anemic_model.supplier_context import ProductSupplierRegion, RegionSupplier
from omni_product.database import Base

if TYPE_CHECKING:
    from omni_product.anemic_model.supplier import Supplier


_ROW_CASCADE = "all, delete-orphan"


class Product(Base):
    __tablename__ = "products"
    # Héritage mono-table : toutes les sous-classes partagent la table `products`.
    __mapper_args__ = {  # noqa: RUF012
        "polymorphic_on": "kind",
        "polymorphic_identity": "standard",
    }

    id: Mapped[str] = mapped_column(String, primary_key=True)
    kind: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    price: Mapped[Price] = composite(
        Price,
        mapped_column("price_base", Float),
        mapped_column("price_tax", Float),
        mapped_column("price_tax_rate", Float),
    )
    kilos: Mapped[float | None] = mapped_column(Float)
    volume: Mapped[str | None] = mapped_column(String)
    quantity: Mapped[int | None] = mapped_column(Integer)
    stock: Mapped[int | None] = mapped_column(Integer)
    warehouse: Mapped[Warehouse] = composite(Warehouse, mapped_column("warehouse_location", String))

    supplier_id: Mapped[str | None] = mapped_column(ForeignKey("suppliers.id"))
    supplier: Mapped[Supplier | None] = relationship(back_populates="products")

    discount_rows: Mapped[list[ProductDiscount]] = relationship(
        cascade=_ROW_CASCADE, order_by=ProductDiscount.id
    )
    image_rows: Mapped[dict[str, ProductImage]] = relationship(
        collection_class=attribute_keyed_dict("image_key"), cascade=_ROW_CASCADE
    )
    supplier_region_rows: Mapped[dict[str, ProductSupplierRegion]] = relationship(
        collection_class=attribute_keyed_dict("region"), cascade=_ROW_CASCADE
    )

    discounts: AssociationProxy[list[str]] = association_proxy(
        "discount_rows", "discount", creator=ProductDiscount
    )
    images: AssociationProxy[dict[str, str | None]] = association_proxy(
        "image_rows", "image_detail", creator=ProductImage
    )
    suppliers_regions: AssociationProxy[dict[str, RegionSupplier]] = association_proxy(
        "supplier_region_rows", "supplier", creator=ProductSupplierRegion
    )

    def is_perishable(self) -> bool:
        # La classe de base connaît sa sous-classe : une branche de plus à chaque nouveau type.
        return isinstance(self, PerishableProduct)


class PerishableProduct(Product):
    """Produit périssable. Ses colonnes sont dans `products`, donc nulles pour les autres types."""

    __mapper_args__ = {"polymorphic_identity": "perishable"}  # noqa: RUF012

    expiration_date: Mapped[date | None] = mapped_column(Date)
    shelf_life_days: Mapped[int | None] = mapped_column(Integer)


class NonExpiringProduct(Product):
    """Produit sans date limite. Aucun champ propre : la classe ne sert qu'à porter un type."""

    __mapper_args__ = {"polymorphic_identity": "non_expiring"}  # noqa: RUF012
