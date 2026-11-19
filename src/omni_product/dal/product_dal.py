from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from omni_product.dal.mapping import (
    product_discounts,
    product_images,
    product_pricing,
    product_sourcing,
    product_storage,
    product_suppliers,
    product_transport,
    products,
)
from omni_product.domain.model.product import (
    Product,
    ProductDiscount,
    ProductImage,
    ProductPricing,
    ProductSourcing,
    ProductStorage,
    ProductSupplierRegion,
    ProductTransport,
)
from omni_product.domain.model.product_values import ProductId, Slug, SupplierId

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


def empty_rows(product: Product, supplier_id: SupplierId | None = None) -> ProductRows:
    """Lignes neuves, sans valeur dans les contextes : elles s'écrivent au premier `save`."""
    product_id = product.id
    return (
        product,
        ProductPricing(id=product_id),
        ProductStorage(id=product_id),
        ProductTransport(id=product_id),
        ProductSourcing(id=product_id, supplier_id=supplier_id),
        [],
        [],
    )


def find_all(session: Session) -> list[ProductRows]:
    found = session.scalars(select(Product).order_by(products.c.id)).all()
    return [_assemble(session, product) for product in found]


def find_by_id(session: Session, product_id: str) -> ProductRows | None:
    product = session.get(Product, ProductId(product_id))
    return None if product is None else _assemble(session, product)


def find_by_slug(session: Session, slug: str) -> ProductRows | None:
    product = session.scalars(select(Product).where(products.c.slug == Slug(slug))).first()
    return None if product is None else _assemble(session, product)


def exists_by_slug(session: Session, slug: str) -> bool:
    return find_by_slug(session, slug) is not None


def save(session: Session, rows: ProductRows) -> ProductRows:
    product, pricing, storage, transport, sourcing, discounts, regions = rows
    product_id = product.id
    saved = session.merge(product)
    # Une ligne par contexte a l'identité du produit : on la fusionne. Les listes se remplacent.
    session.merge(pricing)
    session.merge(storage)
    session.merge(transport)
    session.merge(sourcing)
    _delete_list_rows(session, product_id)
    session.add_all(
        ProductDiscount(id=None, product_id=product_id, discount=discount.discount)
        for discount in discounts
    )
    session.add_all(regions)
    session.add_all(
        ProductImage(id=None, product_id=product_id, image_key=key, image_detail=detail)
        for key, detail in product.images.items()
    )
    session.commit()
    return _assemble(session, saved)


def delete_by_id(session: Session, product_id: str) -> None:
    product = session.get(Product, ProductId(product_id))
    if product is not None:
        _delete_all_rows(session, product.id)
        session.delete(product)
        session.commit()


def delete_by_slug(session: Session, slug: str) -> None:
    product = session.scalars(select(Product).where(products.c.slug == Slug(slug))).first()
    if product is not None:
        delete_by_id(session, product.id.value)


def delete_all(session: Session) -> None:
    for product in session.scalars(select(Product)).all():
        delete_by_id(session, product.id.value)


def _assemble(session: Session, product: Product) -> ProductRows:
    product_id = product.id
    _, pricing, storage, transport, sourcing, _, _ = empty_rows(product)
    product.images = {
        row.image_key: row.image_detail
        for row in session.scalars(
            select(ProductImage).where(product_images.c.product_id == product_id)
        )
    }
    return (
        product,
        session.get(ProductPricing, product_id) or pricing,
        session.get(ProductStorage, product_id) or storage,
        session.get(ProductTransport, product_id) or transport,
        session.get(ProductSourcing, product_id) or sourcing,
        list(
            session.scalars(
                select(ProductDiscount)
                .where(product_discounts.c.product_id == product_id)
                .order_by(product_discounts.c.id)
            )
        ),
        list(
            session.scalars(
                select(ProductSupplierRegion).where(product_suppliers.c.product_id == product_id)
            )
        ),
    )


def _delete_list_rows(session: Session, product_id: ProductId) -> None:
    session.execute(delete(ProductDiscount).where(product_discounts.c.product_id == product_id))
    session.execute(
        delete(ProductSupplierRegion).where(product_suppliers.c.product_id == product_id)
    )
    session.execute(delete(ProductImage).where(product_images.c.product_id == product_id))


def _delete_all_rows(session: Session, product_id: ProductId) -> None:
    _delete_list_rows(session, product_id)
    session.execute(delete(ProductPricing).where(product_pricing.c.product_id == product_id))
    session.execute(delete(ProductStorage).where(product_storage.c.product_id == product_id))
    session.execute(delete(ProductTransport).where(product_transport.c.product_id == product_id))
    session.execute(delete(ProductSourcing).where(product_sourcing.c.product_id == product_id))
