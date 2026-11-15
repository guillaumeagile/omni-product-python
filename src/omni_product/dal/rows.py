"""Les lignes de la base : la seule couche qui connaît SQLAlchemy. Le modèle n'en sait rien.

Chaque table garde son nom et ses colonnes. Les conversions entre lignes et modèle sont dans
`product_dal.py` et `supplier_dal.py`.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from omni_product.database import Base, record_column
from omni_product.domain.model import (
    Amount,
    ContactEmail,
    ContactPhone,
    Country,
    Discount,
    ImageDetail,
    ImageKey,
    Kilos,
    Location,
    ProductId,
    Quantity,
    Rate,
    Region,
    Siren,
    Slug,
    Stock,
    SupplierId,
    TvaId,
    Volume,
)

_ROW_CASCADE = "all, delete-orphan"


class ProductImageRow(Base):
    __tablename__ = "product_images"

    product_id: Mapped[ProductId] = mapped_column(
        record_column(ProductId), ForeignKey("products.id"), primary_key=True
    )
    image_key: Mapped[ImageKey] = mapped_column(record_column(ImageKey), primary_key=True)
    image_detail: Mapped[ImageDetail | None] = mapped_column(record_column(ImageDetail))


class ProductRow(Base):
    __tablename__ = "products"

    id: Mapped[ProductId] = mapped_column(record_column(ProductId), primary_key=True)
    # `standard`, `perishable` ou `non_expiring` : une seule table pour les trois types.
    kind: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[Slug] = mapped_column(record_column(Slug), unique=True, nullable=False)
    expiration_date: Mapped[date | None] = mapped_column(Date)
    shelf_life_days: Mapped[int | None] = mapped_column(Integer)

    image_rows: Mapped[list[ProductImageRow]] = relationship(cascade=_ROW_CASCADE)


class ProductPriceRow(Base):
    __tablename__ = "product_prices"

    product_id: Mapped[ProductId] = mapped_column(
        record_column(ProductId), ForeignKey("products.id"), primary_key=True
    )
    base: Mapped[Amount | None] = mapped_column(record_column(Amount, Float))
    tax: Mapped[Amount | None] = mapped_column(record_column(Amount, Float))
    tax_rate: Mapped[Rate | None] = mapped_column(record_column(Rate, Float))


class ProductDiscountRow(Base):
    __tablename__ = "product_discounts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[ProductId] = mapped_column(
        record_column(ProductId), ForeignKey("products.id")
    )
    discount: Mapped[Discount] = mapped_column(record_column(Discount))


class ProductTransportRow(Base):
    __tablename__ = "product_transports"

    product_id: Mapped[ProductId] = mapped_column(record_column(ProductId), primary_key=True)
    kilos: Mapped[Kilos | None] = mapped_column(record_column(Kilos, Float))
    volume: Mapped[Volume | None] = mapped_column(record_column(Volume))


class ProductStockRow(Base):
    __tablename__ = "product_stocks"

    product_id: Mapped[ProductId] = mapped_column(record_column(ProductId), primary_key=True)
    quantity: Mapped[Quantity | None] = mapped_column(record_column(Quantity, Integer))
    stock: Mapped[Stock | None] = mapped_column(record_column(Stock, Integer))
    warehouse_location: Mapped[Location | None] = mapped_column(record_column(Location))


class ProductSupplyRow(Base):
    __tablename__ = "product_supplies"

    product_id: Mapped[ProductId] = mapped_column(
        record_column(ProductId), ForeignKey("products.id"), primary_key=True
    )
    supplier_id: Mapped[SupplierId | None] = mapped_column(
        record_column(SupplierId), ForeignKey("suppliers.id")
    )


class ProductSupplierRegionRow(Base):
    __tablename__ = "product_suppliers"

    product_id: Mapped[ProductId] = mapped_column(
        record_column(ProductId), ForeignKey("products.id"), primary_key=True
    )
    region: Mapped[Region] = mapped_column(record_column(Region), primary_key=True)
    name: Mapped[str | None] = mapped_column(String)
    siren: Mapped[Siren | None] = mapped_column(record_column(Siren))
    tva_id: Mapped[TvaId | None] = mapped_column(record_column(TvaId))


class SupplierRow(Base):
    __tablename__ = "suppliers"

    id: Mapped[SupplierId] = mapped_column(record_column(SupplierId), primary_key=True)
    name: Mapped[str | None] = mapped_column(String)
    contact_email: Mapped[ContactEmail | None] = mapped_column(record_column(ContactEmail))
    contact_phone: Mapped[ContactPhone | None] = mapped_column(record_column(ContactPhone))
    country: Mapped[Country | None] = mapped_column(record_column(Country))
    region: Mapped[Region | None] = mapped_column(record_column(Region))
