from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from omni_product.anemic_model import (
    Product,
    ProductDiscount,
    ProductPricing,
    ProductSourcing,
    ProductStorage,
    ProductSupplierRegion,
    ProductTransport,
)

# Un produit et les lignes de ses contextes, dans l'ordre : produit (Catalog), prix (Pricing),
# stock (Storage), transport, fournisseur principal, remises (Pricing), fournisseurs par région.
# Un tuple et non une classe : aucune classe du modèle ne mêle les contextes.
type ProductRows = tuple[
    Product,
    ProductPricing,
    ProductStorage,
    ProductTransport,
    ProductSourcing,
    list[ProductDiscount],
    list[ProductSupplierRegion],
]


def empty_rows(product: Product, supplier_id: str | None = None) -> ProductRows:
    """Lignes neuves, sans valeur dans les contextes : elles s'écrivent au premier `save`."""
    product_id = product.id
    return (
        product,
        ProductPricing(product_id=product_id),
        ProductStorage(product_id=product_id),
        ProductTransport(product_id=product_id),
        ProductSourcing(product_id=product_id, supplier_id=supplier_id),
        [],
        [],
    )


def find_all(session: Session) -> list[ProductRows]:
    products = session.scalars(select(Product).order_by(Product.id)).all()
    return [_assemble(session, product) for product in products]


def find_by_id(session: Session, product_id: str) -> ProductRows | None:
    product = session.get(Product, product_id)
    return None if product is None else _assemble(session, product)


def find_by_slug(session: Session, slug: str) -> ProductRows | None:
    product = session.scalars(select(Product).where(Product.slug == slug)).first()
    return None if product is None else _assemble(session, product)


def exists_by_slug(session: Session, slug: str) -> bool:
    return find_by_slug(session, slug) is not None


def save(session: Session, rows: ProductRows) -> ProductRows:
    product, pricing, storage, transport, sourcing, discounts, regions = rows
    product_id = product.id
    saved = session.merge(product)
    session.merge(pricing)
    session.merge(storage)
    session.merge(transport)
    session.merge(sourcing)
    # Les listes (remises, fournisseurs par région) se remplacent en entier, comme avant.
    _delete_list_rows(session, product_id)
    session.add_all(discounts)
    session.add_all(regions)
    session.commit()
    return _assemble(session, saved)


def delete_by_id(session: Session, product_id: str) -> None:
    product = session.get(Product, product_id)
    if product is not None:
        _delete_all_rows(session, product_id)
        session.delete(product)
        session.commit()


def delete_by_slug(session: Session, slug: str) -> None:
    product = session.scalars(select(Product).where(Product.slug == slug)).first()
    if product is not None:
        delete_by_id(session, product.id)


def delete_all(session: Session) -> None:
    for product in session.scalars(select(Product)).all():
        delete_by_id(session, product.id)


def _assemble(session: Session, product: Product) -> ProductRows:
    product_id = product.id
    _, pricing, storage, transport, sourcing, _, _ = empty_rows(product)
    return (
        product,
        session.get(ProductPricing, product_id) or pricing,
        session.get(ProductStorage, product_id) or storage,
        session.get(ProductTransport, product_id) or transport,
        session.get(ProductSourcing, product_id) or sourcing,
        list(
            session.scalars(
                select(ProductDiscount)
                .where(ProductDiscount.product_id == product_id)
                .order_by(ProductDiscount.id)
            )
        ),
        list(
            session.scalars(
                select(ProductSupplierRegion).where(ProductSupplierRegion.product_id == product_id)
            )
        ),
    )


def _delete_list_rows(session: Session, product_id: str) -> None:
    session.execute(delete(ProductDiscount).where(ProductDiscount.product_id == product_id))
    session.execute(
        delete(ProductSupplierRegion).where(ProductSupplierRegion.product_id == product_id)
    )


def _delete_all_rows(session: Session, product_id: str) -> None:
    _delete_list_rows(session, product_id)
    session.execute(delete(ProductPricing).where(ProductPricing.product_id == product_id))
    session.execute(delete(ProductStorage).where(ProductStorage.product_id == product_id))
    session.execute(delete(ProductTransport).where(ProductTransport.product_id == product_id))
    session.execute(delete(ProductSourcing).where(ProductSourcing.product_id == product_id))
