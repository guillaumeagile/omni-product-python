from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from omni_product.anemic_model import ProductSupplierRegion, RegionSupplier


def find_by_product_id(session: Session, product_id: str) -> dict[str, RegionSupplier]:
    rows = session.scalars(
        select(ProductSupplierRegion).where(ProductSupplierRegion.product_id == product_id)
    )
    return {row.region: row.supplier for row in rows}


def replace_regions(session: Session, product_id: str, regions: dict[str, RegionSupplier]) -> None:
    """Remplace les fournisseurs régionaux du produit (comme `PUT` en Java)."""
    session.execute(
        delete(ProductSupplierRegion).where(ProductSupplierRegion.product_id == product_id)
    )
    session.add_all(
        [
            ProductSupplierRegion(product_id, region, supplier)
            for region, supplier in regions.items()
        ]
    )
    session.commit()
