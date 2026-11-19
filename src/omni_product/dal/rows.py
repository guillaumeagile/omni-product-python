"""Lignes de la base : le schéma SQL, sans rien du modèle métier.

Les tables et colonnes sont celles d'avant la règle 3 : seul l'endroit où elles sont
décrites change. La conversion avec le modèle métier est dans `conversion.py`.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm.collections import attribute_keyed_dict

from omni_product.database import Base


class SupplierRow(Base):
    __tablename__ = "suppliers"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str | None] = mapped_column(String)
    contact_email: Mapped[str | None] = mapped_column(String)
    contact_phone: Mapped[str | None] = mapped_column(String)
    country: Mapped[str | None] = mapped_column(String)
    region: Mapped[str | None] = mapped_column(String)


class ProductImageRow(Base):
    __tablename__ = "product_images"

    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), primary_key=True)
    image_key: Mapped[str] = mapped_column(String, primary_key=True)
    image_detail: Mapped[str | None] = mapped_column(String)


class ProductRow(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    # Une seule table pour toutes les variantes : `kind` dit laquelle.
    kind: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    supplier_id: Mapped[str | None] = mapped_column(ForeignKey("suppliers.id"))
    # Colonnes de la variante périssable, nulles pour les autres types.
    expiration_date: Mapped[date | None] = mapped_column(Date)
    shelf_life_days: Mapped[int | None] = mapped_column(Integer)

    image_rows: Mapped[dict[str, ProductImageRow]] = relationship(
        collection_class=attribute_keyed_dict("image_key"), cascade="all, delete-orphan"
    )


class ProductPriceRow(Base):
    __tablename__ = "product_price"

    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), primary_key=True)
    price_base: Mapped[float | None] = mapped_column(Float)
    price_tax: Mapped[float | None] = mapped_column(Float)
    price_tax_rate: Mapped[float | None] = mapped_column(Float)


class ProductDiscountRow(Base):
    __tablename__ = "product_discounts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"))
    discount: Mapped[str] = mapped_column(String)


class ProductShipmentRow(Base):
    __tablename__ = "product_shipment"

    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), primary_key=True)
    kilos: Mapped[float | None] = mapped_column(Float)
    volume: Mapped[str | None] = mapped_column(String)


class ProductStockRow(Base):
    __tablename__ = "product_stock"

    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), primary_key=True)
    quantity: Mapped[int | None] = mapped_column(Integer)
    stock: Mapped[int | None] = mapped_column(Integer)
    warehouse_location: Mapped[str | None] = mapped_column(String)


class ProductSupplierRegionRow(Base):
    __tablename__ = "product_suppliers"

    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), primary_key=True)
    region: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str | None] = mapped_column(String)
    siren: Mapped[str | None] = mapped_column(String)
    tva_id: Mapped[str | None] = mapped_column(String)
