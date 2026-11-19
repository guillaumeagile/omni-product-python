from dataclasses import dataclass

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, composite, mapped_column

from omni_product.database import Base


@dataclass(frozen=True)
class RegionSupplier:
    """Fournisseur embarqué pour une région commerciale."""

    name: str | None = None
    siren: str | None = None
    tva_id: str | None = None


@dataclass(frozen=True)
class SupplierContext:
    supplier_id: str | None
    suppliers_by_region: dict[str, RegionSupplier]


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
