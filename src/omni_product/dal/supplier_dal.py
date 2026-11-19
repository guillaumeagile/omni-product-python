from sqlalchemy import ForeignKey, String, select
from sqlalchemy import delete as delete_rows
from sqlalchemy.orm import Mapped, Session, composite, mapped_column

from omni_product.dal.model_mapping import products, suppliers
from omni_product.database import Base
from omni_product.domain.model.product import RegionSupplier
from omni_product.domain.model.supplier import Supplier


class ProductSupplierRegion(Base):
    """Contexte Supplier : le fournisseur d'un produit par région, lié par `product_id`."""

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


def find_all(session: Session) -> list[Supplier]:
    return list(session.scalars(select(Supplier).order_by(suppliers.c.id)))


def find_by_id(session: Session, supplier_id: str) -> Supplier | None:
    return session.get(Supplier, supplier_id)


def find_by_country(session: Session, country: str) -> list[Supplier]:
    return _find_all_where(session, suppliers.c.country == country)


def find_by_region(session: Session, region: str) -> list[Supplier]:
    return _find_all_where(session, suppliers.c.region == region)


def find_by_name(session: Session, name: str) -> Supplier | None:
    return session.scalars(select(Supplier).where(suppliers.c.name == name)).first()


def find_by_product_id(session: Session, product_id: str) -> list[Supplier]:
    """Requête SQL à la place du filtrage en mémoire qui causait le lazy loading Java."""
    supplier_ids = select(products.c.supplier_id).where(products.c.id == product_id)
    return _find_all_where(session, suppliers.c.id.in_(supplier_ids))


def find_regions(session: Session, product_id: str) -> dict[str, RegionSupplier]:
    statement = select(ProductSupplierRegion).where(ProductSupplierRegion.product_id == product_id)
    return {row.region: row.supplier for row in session.scalars(statement)}


def replace_regions(
    session: Session, product_id: str, suppliers_regions: dict[str, RegionSupplier]
) -> None:
    delete_regions_for(session, product_id)
    session.add_all(
        ProductSupplierRegion(product_id=product_id, region=region, supplier=supplier)
        for region, supplier in suppliers_regions.items()
    )


def delete_regions_for(session: Session, product_id: str) -> None:
    session.execute(
        delete_rows(ProductSupplierRegion).where(ProductSupplierRegion.product_id == product_id)
    )


def save(session: Session, supplier: Supplier) -> Supplier:
    saved = session.merge(supplier)
    session.commit()
    return saved


def delete(session: Session, supplier: Supplier) -> None:
    session.delete(supplier)
    session.commit()


def delete_all(session: Session) -> None:
    for supplier in find_all(session):
        session.delete(supplier)
    session.commit()


def _find_all_where(session: Session, criterion: object) -> list[Supplier]:
    statement = select(Supplier).where(criterion).order_by(suppliers.c.id)  # pyright: ignore[reportArgumentType]
    return list(session.scalars(statement))
