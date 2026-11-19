from sqlalchemy import select
from sqlalchemy.orm import Session

from omni_product.anemic_model import (
    Product,
    ProductPricing,
    ProductStorage,
    ProductSupplierContext,
    ProductTransport,
)

type ProductRecord = tuple[
    Product,
    ProductPricing | None,
    ProductStorage | None,
    ProductTransport | None,
    ProductSupplierContext | None,
]


def find_all(session: Session) -> list[Product]:
    return list(session.scalars(select(Product).order_by(Product.id)))


def find_by_id(session: Session, product_id: str) -> Product | None:
    return session.get(Product, product_id)


def find_all_records(session: Session) -> list[ProductRecord]:
    products = find_all(session)
    if not products:
        return []

    product_ids = [product.id for product in products]
    pricing_by_id = {
        row.product_id: row
        for row in session.scalars(
            select(ProductPricing).where(ProductPricing.product_id.in_(product_ids))
        )
    }
    storage_by_id = {
        row.product_id: row
        for row in session.scalars(
            select(ProductStorage).where(ProductStorage.product_id.in_(product_ids))
        )
    }
    transport_by_id = {
        row.product_id: row
        for row in session.scalars(
            select(ProductTransport).where(ProductTransport.product_id.in_(product_ids))
        )
    }
    supplier_by_id = {
        row.product_id: row
        for row in session.scalars(
            select(ProductSupplierContext).where(ProductSupplierContext.product_id.in_(product_ids))
        )
    }
    return [
        (
            product,
            pricing_by_id.get(product.id),
            storage_by_id.get(product.id),
            transport_by_id.get(product.id),
            supplier_by_id.get(product.id),
        )
        for product in products
    ]


def find_record_by_id(session: Session, product_id: str) -> ProductRecord | None:
    product = find_by_id(session, product_id)
    if product is None:
        return None
    return (
        product,
        session.get(ProductPricing, product_id),
        session.get(ProductStorage, product_id),
        session.get(ProductTransport, product_id),
        session.get(ProductSupplierContext, product_id),
    )


def find_by_slug(session: Session, slug: str) -> Product | None:
    return session.scalars(select(Product).where(Product.slug == slug)).first()


def exists_by_slug(session: Session, slug: str) -> bool:
    return find_by_slug(session, slug) is not None


def save(session: Session, product: Product) -> Product:
    saved = session.merge(product)
    session.commit()
    return saved


def save_record(session: Session, record: ProductRecord) -> ProductRecord:
    product, pricing, storage, transport, supplier = record
    saved_product = session.merge(product)
    saved_pricing = session.merge(pricing) if pricing is not None else None
    saved_storage = session.merge(storage) if storage is not None else None
    saved_transport = session.merge(transport) if transport is not None else None
    saved_supplier = session.merge(supplier) if supplier is not None else None
    session.commit()
    return saved_product, saved_pricing, saved_storage, saved_transport, saved_supplier


def delete_by_id(session: Session, product_id: str) -> None:
    product = find_by_id(session, product_id)
    if product is not None:
        _delete_context_rows(session, product_id)
        session.delete(product)
        session.commit()


def delete_by_slug(session: Session, slug: str) -> None:
    product = find_by_slug(session, slug)
    if product is not None:
        delete_by_id(session, product.id)


def delete_all(session: Session) -> None:
    for product in find_all(session):
        _delete_context_rows(session, product.id)
        session.delete(product)
    session.commit()


def _delete_context_rows(session: Session, product_id: str) -> None:
    for model in (ProductPricing, ProductStorage, ProductTransport, ProductSupplierContext):
        context = session.get(model, product_id)
        if context is not None:
            session.delete(context)
