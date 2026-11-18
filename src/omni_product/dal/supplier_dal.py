from sqlalchemy import ColumnElement, select
from sqlalchemy.orm import Session

from omni_product.dal import product_dal
from omni_product.dal.rows import ProductSupplyRow, SupplierRow
from omni_product.domain.model import Country, ProductId, Region, Supplier, SupplierId


def find_all(session: Session) -> list[Supplier]:
    rows = session.scalars(select(SupplierRow).order_by(SupplierRow.id)).all()
    return [_supplier(row) for row in rows]


def find_by_id(session: Session, supplier_id: SupplierId) -> Supplier | None:
    row = session.get(SupplierRow, supplier_id)
    return None if row is None else _supplier(row)


def find_by_country(session: Session, country: Country) -> list[Supplier]:
    return _find_all_where(session, SupplierRow.country == country)


def find_by_region(session: Session, region: Region) -> list[Supplier]:
    return _find_all_where(session, SupplierRow.region == region)


def find_by_name(session: Session, name: str) -> Supplier | None:
    row = session.scalars(select(SupplierRow).where(SupplierRow.name == name)).first()
    return None if row is None else _supplier(row)


def find_by_product_id(session: Session, product_id: ProductId) -> list[Supplier]:
    """Requête SQL à la place du filtrage en mémoire qui causait le lazy loading Java."""
    supplier_ids = select(ProductSupplyRow.supplier_id).where(
        ProductSupplyRow.product_id == product_id
    )
    return _find_all_where(session, SupplierRow.id.in_(supplier_ids))


def save(session: Session, supplier: Supplier) -> Supplier:
    row = session.merge(_supplier_row(supplier))
    session.commit()
    return _supplier(row)


def delete(session: Session, supplier: Supplier) -> None:
    # Comportement conservé : supprimer un fournisseur supprime les produits qu'il fournit.
    product_ids = session.scalars(
        select(ProductSupplyRow.product_id).where(ProductSupplyRow.supplier_id == supplier.id)
    ).all()
    for product_id in product_ids:
        product_dal.delete_by_id(session, product_id)
    row = session.get(SupplierRow, supplier.id)
    if row is not None:
        session.delete(row)
    session.commit()


def delete_all(session: Session) -> None:
    for row in session.scalars(select(SupplierRow)).all():
        session.delete(row)
    session.commit()


def _find_all_where(session: Session, criterion: ColumnElement[bool]) -> list[Supplier]:
    rows = session.scalars(select(SupplierRow).where(criterion).order_by(SupplierRow.id)).all()
    return [_supplier(row) for row in rows]


def _supplier(row: SupplierRow) -> Supplier:
    return Supplier(
        id=row.id,
        name=row.name,
        contact_email=row.contact_email,
        contact_phone=row.contact_phone,
        country=row.country,
        region=row.region,
    )


def _supplier_row(supplier: Supplier) -> SupplierRow:
    return SupplierRow(
        id=supplier.id,
        name=supplier.name,
        contact_email=supplier.contact_email,
        contact_phone=supplier.contact_phone,
        country=supplier.country,
        region=supplier.region,
    )
