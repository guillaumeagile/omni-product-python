from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from omni_product.dal.conversion import region_from_row, regions_to_rows
from omni_product.dal.rows import ProductSupplierRegionRow
from omni_product.domain.model.supplier_region import RegionSupplier


def find_by_product_id(session: Session, product_id: str) -> dict[str, RegionSupplier]:
    rows = session.scalars(
        select(ProductSupplierRegionRow).where(ProductSupplierRegionRow.product_id == product_id)
    )
    return {row.region: region_from_row(row) for row in rows}


def replace_regions(session: Session, product_id: str, regions: dict[str, RegionSupplier]) -> None:
    """Remplace les fournisseurs régionaux du produit (comme `PUT` en Java)."""
    session.execute(
        delete(ProductSupplierRegionRow).where(ProductSupplierRegionRow.product_id == product_id)
    )
    session.add_all(regions_to_rows(product_id, regions))
    session.commit()
