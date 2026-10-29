from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.orm import Mapped, composite, mapped_column, relationship
from sqlalchemy.orm.collections import attribute_keyed_dict

from omni_product.database import Base

if TYPE_CHECKING:
    from omni_product.model.supplier import Supplier


# Équivalents des @Embeddable Java : des composites SQLAlchemy mis à plat dans la table parente.
@dataclass
class Price:
    base: float | None = None
    tax: float | None = None
    tax_rate: float | None = None


@dataclass
class Warehouse:
    location: str | None = None


@dataclass
class RegionSupplier:
    """`Product.Supplier` en Java : fournisseur embarqué, par région."""

    name: str | None = None
    siren: str | None = None
    tva_id: str | None = None


# Équivalents des @ElementCollection + @CollectionTable.
class ProductDiscount(Base):
    __tablename__ = "product_discounts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"))
    discount: Mapped[str] = mapped_column(String)

    def __init__(self, discount: str) -> None:
        self.discount = discount


class ProductImage(Base):
    __tablename__ = "product_images"

    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), primary_key=True)
    image_key: Mapped[str] = mapped_column(String, primary_key=True)
    image_detail: Mapped[str | None] = mapped_column(String)

    def __init__(self, image_key: str, image_detail: str | None) -> None:
        self.image_key = image_key
        self.image_detail = image_detail


class ProductSupplierRegion(Base):
    __tablename__ = "product_suppliers"

    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), primary_key=True)
    region: Mapped[str] = mapped_column(String, primary_key=True)
    supplier: Mapped[RegionSupplier] = composite(
        RegionSupplier,
        mapped_column("name", String),
        mapped_column("siren", String),
        mapped_column("tva_id", String),
    )

    def __init__(self, region: str, supplier: RegionSupplier) -> None:
        self.region = region
        self.supplier = supplier


_ROW_CASCADE = "all, delete-orphan"


class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String, primary_key=True)
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
