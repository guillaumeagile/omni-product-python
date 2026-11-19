from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, composite, mapped_column

from omni_product.database import Base


@dataclass
class RegionSupplier:
    """`Product.Supplier` en Java : fournisseur embarqué, par région."""

    name: str | None = None
    siren: str | None = None
    tva_id: str | None = None


class ProductSupplierRegion(Base):
    """Le fournisseur d'un produit dans une région : une ligne par (produit, région)."""

    __tablename__ = "product_suppliers"

    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), primary_key=True)
    region: Mapped[str] = mapped_column(String, primary_key=True)
    supplier: Mapped[RegionSupplier] = composite(
        RegionSupplier,
        mapped_column("name", String),
        mapped_column("siren", String),
        mapped_column("tva_id", String),
    )

    def __init__(self, product_id: str, region: str, supplier: RegionSupplier) -> None:
        self.product_id = product_id
        self.region = region
        self.supplier = supplier
