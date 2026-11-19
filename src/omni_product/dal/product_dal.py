from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from omni_product.anemic_model import (
    Product,
    ProductAggregate,
    ProductDiscount,
    ProductPricing,
    ProductSourcing,
    ProductStorage,
    ProductSupplierRegion,
    ProductTransport,
)


def find_all(session: Session) -> list[ProductAggregate]:
    products = session.scalars(select(Product).order_by(Product.id)).all()
    return [_assemble(session, product) for product in products]


def find_by_id(session: Session, product_id: str) -> ProductAggregate | None:
    product = session.get(Product, product_id)
    return None if product is None else _assemble(session, product)


def find_by_slug(session: Session, slug: str) -> ProductAggregate | None:
    product = session.scalars(select(Product).where(Product.slug == slug)).first()
    return None if product is None else _assemble(session, product)


def exists_by_slug(session: Session, slug: str) -> bool:
    return find_by_slug(session, slug) is not None


def save(session: Session, aggregate: ProductAggregate) -> ProductAggregate:
    product_id = aggregate.product.id
    session.merge(aggregate.product)
    session.merge(aggregate.pricing)
    session.merge(aggregate.storage)
    session.merge(aggregate.transport)
    session.merge(aggregate.sourcing)
    # Les listes (remises, fournisseurs par région) se remplacent en entier, comme avant.
    _delete_list_rows(session, product_id)
    session.add_all(aggregate.discounts)
    session.add_all(aggregate.suppliers_regions)
    session.commit()
    return _assemble(session, aggregate.product)


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


def _assemble(session: Session, product: Product) -> ProductAggregate:
    product_id = product.id
    aggregate = ProductAggregate.of(product)
    aggregate.pricing = session.get(ProductPricing, product_id) or aggregate.pricing
    aggregate.storage = session.get(ProductStorage, product_id) or aggregate.storage
    aggregate.transport = session.get(ProductTransport, product_id) or aggregate.transport
    aggregate.sourcing = session.get(ProductSourcing, product_id) or aggregate.sourcing
    aggregate.discounts = list(
        session.scalars(
            select(ProductDiscount)
            .where(ProductDiscount.product_id == product_id)
            .order_by(ProductDiscount.id)
        )
    )
    aggregate.suppliers_regions = list(
        session.scalars(
            select(ProductSupplierRegion).where(ProductSupplierRegion.product_id == product_id)
        )
    )
    return aggregate


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
