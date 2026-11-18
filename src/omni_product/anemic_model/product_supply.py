from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import ForeignKey, String
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.orm import Mapped, composite, mapped_column, relationship
from sqlalchemy.orm.collections import attribute_keyed_dict

from omni_product.database import Base

_ROW_CASCADE = "all, delete-orphan"


@dataclass
class RegionSupplier:
    """`Product.Supplier` en Java : fournisseur embarqué, par région."""

    name: str | None = None
    siren: str | None = None
    tva_id: str | None = None


class ProductSupplierRegion(Base):
    __tablename__ = "product_suppliers"

    product_id: Mapped[str] = mapped_column(
        ForeignKey("product_supplies.product_id"), primary_key=True
    )
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


class ProductSupply(Base):
    """Les fournisseurs d'un produit, dans le contexte Supplier. Lié au produit par `product_id`."""

    __tablename__ = "product_supplies"

    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), primary_key=True)
    supplier_id: Mapped[str | None] = mapped_column(ForeignKey("suppliers.id"))

    supplier_region_rows: Mapped[dict[str, ProductSupplierRegion]] = relationship(
        collection_class=attribute_keyed_dict("region"), cascade=_ROW_CASCADE
    )
    suppliers_regions: AssociationProxy[dict[str, RegionSupplier]] = association_proxy(
        "supplier_region_rows", "supplier", creator=ProductSupplierRegion
    )
