from __future__ import annotations

from datetime import date

from result import Err, Ok, Result
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from omni_product.dal.records import raw
from omni_product.dal.rows import (
    ProductDiscountRow,
    ProductImageRow,
    ProductPriceRow,
    ProductRow,
    ProductStockRow,
    ProductSupplierRegionRow,
    ProductSupplyRow,
    ProductTransportRow,
)
from omni_product.domain.model import (
    Amount,
    NonExpiring,
    ParDateEtDuree,
    ParDateLimite,
    ParDureeDeConservation,
    Perishable,
    Price,
    PrixAvecTaxe,
    PrixHorsTaxe,
    Product,
    ProductId,
    ProductImage,
    ProductPrice,
    ProductStock,
    ProductSupply,
    ProductTransport,
    Quantity,
    Rate,
    ShelfLife,
    Slug,
    Stock,
    SupplierByRegion,
    Warehouse,
    charge_of,
    perissable_of,
    prix_of,
    region_supplier_of,
)
from omni_product.domain.model.errors import InvalidValueError
from omni_product.domain.model.product_sheet import ProductSheet


class SqlProductRepository:
    """Implémente `ProductRepository` avec SQLAlchemy : l'adaptateur de persistance du catalogue."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def find_all(self) -> list[ProductSheet]:
        return find_all(self._session)

    def find_by_id(self, product_id: ProductId) -> ProductSheet | None:
        return find_by_id(self._session, product_id)

    def save(self, sheet: ProductSheet) -> ProductSheet:
        return save(self._session, sheet)

    def delete_by_id(self, product_id: ProductId) -> None:
        delete_by_id(self._session, product_id)


def find_all(session: Session) -> list[ProductSheet]:
    rows = session.scalars(select(ProductRow).order_by(ProductRow.id)).all()
    return [_load(session, row) for row in rows]


def find_by_id(session: Session, product_id: ProductId) -> ProductSheet | None:
    row = session.get(ProductRow, product_id)
    return None if row is None else _load(session, row)


def find_by_slug(session: Session, slug: Slug) -> Product | None:
    row = session.scalars(select(ProductRow).where(ProductRow.slug == slug)).first()
    return None if row is None else _product(row)


def exists_by_slug(session: Session, slug: Slug) -> bool:
    return find_by_slug(session, slug) is not None


def save(session: Session, sheet: ProductSheet) -> ProductSheet:
    row = session.merge(_product_row(sheet.product))
    _replace_context_rows(session, sheet)
    session.commit()
    return _load(session, row)


def delete_by_id(session: Session, product_id: ProductId) -> None:
    row = session.get(ProductRow, product_id)
    if row is not None:
        _delete_context_rows(session, product_id)
        session.delete(row)
        session.commit()


def delete_by_slug(session: Session, slug: Slug) -> None:
    row = session.scalars(select(ProductRow).where(ProductRow.slug == slug)).first()
    if row is not None:
        delete_by_id(session, row.id)


def delete_all(session: Session) -> None:
    for row in session.scalars(select(ProductRow)).all():
        delete_by_id(session, row.id)


def _product(row: ProductRow) -> Product:
    images = tuple(
        ProductImage(key=image.image_key, detail=image.image_detail) for image in row.image_rows
    )
    match row.kind:
        case "perishable":
            shelf_life: ShelfLife | None = _valeur(
                perissable_of(row.expiration_date, row.shelf_life_days)
            )
        case "non_expiring":
            shelf_life = NonExpiring()
        case _:
            shelf_life = None
    return Product(id=row.id, name=row.name, slug=row.slug, images=images, shelf_life=shelf_life)


def _colonnes_de_la_durée(perishable: Perishable | None) -> tuple[date | None, int | None]:
    """La date limite et la durée de conservation, telles qu'elles se stockent."""
    match perishable:
        case ParDateLimite(expiration_date=date_limite):
            return date_limite, None
        case ParDureeDeConservation(shelf_life_days=duree):
            return None, duree.value
        case ParDateEtDuree(expiration_date=date_limite, shelf_life_days=duree):
            return date_limite, duree.value
        case None:
            return None, None


def _product_row(product: Product) -> ProductRow:
    perishable = product.shelf_life if isinstance(product.shelf_life, Perishable) else None
    expiration_date, shelf_life_days = _colonnes_de_la_durée(perishable)
    return ProductRow(
        id=product.id,
        kind=_kind_of(product),
        name=product.name,
        slug=product.slug,
        expiration_date=expiration_date,
        shelf_life_days=shelf_life_days,
        image_rows=[
            ProductImageRow(product_id=product.id, image_key=image.key, image_detail=image.detail)
            for image in product.images
        ],
    )


def _kind_of(product: Product) -> str:
    match product.shelf_life:
        case ParDateLimite() | ParDureeDeConservation() | ParDateEtDuree():
            return "perishable"
        case NonExpiring():
            return "non_expiring"
        case None:
            return "standard"


def _valeur[T](resultat: Result[T, InvalidValueError]) -> T:
    """La valeur d'un résultat lu en base : une ligne incohérente lève une erreur."""
    match resultat:
        case Ok(valeur):
            return valeur
        case Err(erreur):
            raise ValueError(f"Donnée incohérente en base : {erreur}")


def _load(session: Session, row: ProductRow) -> ProductSheet:
    product_id = row.id
    price = session.get(ProductPriceRow, product_id)
    discounts = session.scalars(
        select(ProductDiscountRow)
        .where(ProductDiscountRow.product_id == product_id)
        .order_by(ProductDiscountRow.id)
    ).all()
    transport = session.get(ProductTransportRow, product_id)
    stock = session.get(ProductStockRow, product_id)
    supply = session.get(ProductSupplyRow, product_id)
    regions = session.scalars(
        select(ProductSupplierRegionRow).where(ProductSupplierRegionRow.product_id == product_id)
    ).all()
    return ProductSheet(
        product=_product(row),
        pricing=ProductPrice(
            id=product_id,
            price=(
                _valeur(prix_of(raw(price.base), raw(price.tax), raw(price.tax_rate)))
                if price is not None
                else None
            ),
            discounts=tuple(line.discount for line in discounts),
        ),
        transport=ProductTransport(
            id=product_id,
            kilos_volume=(
                _valeur(charge_of(raw(transport.kilos), raw(transport.volume)))
                if transport is not None
                else None
            ),
        ),
        stock=_stock(product_id, stock),
        supply=ProductSupply(
            id=product_id,
            supplier_id=supply.supplier_id if supply is not None else None,
            regions=tuple(
                SupplierByRegion(
                    region=line.region,
                    supplier=_valeur(
                        region_supplier_of(line.name, raw(line.siren), raw(line.tva_id))
                    ),
                )
                for line in regions
            ),
        ),
    )


def _stock(product_id: ProductId, stock: ProductStockRow | None) -> ProductStock | None:
    """Le stock du produit, ou `None` sans ligne. Sans quantité saisie, elle vaut le stock."""
    if stock is None:
        return None
    valeur_stock = stock.stock if stock.stock is not None else Stock(0)
    quantite = stock.quantity if stock.quantity is not None else Quantity(valeur_stock.value)
    return ProductStock(
        id=product_id,
        quantity=quantite,
        stock=valeur_stock,
        warehouse=(
            Warehouse(stock.warehouse_location) if stock.warehouse_location is not None else None
        ),
    )


def _colonnes_du_prix(price: Price) -> tuple[Amount, Amount | None, Rate | None]:
    """Le prix de base, puis la taxe et son taux, tels qu'ils se stockent."""
    match price:
        case PrixHorsTaxe(base=base):
            return base, None, None
        case PrixAvecTaxe(base=base, tax=tax, tax_rate=tax_rate):
            return base, tax, tax_rate


def _replace_context_rows(session: Session, sheet: ProductSheet) -> None:
    """Remplace les lignes des contextes : une sauvegarde écrase l'ancienne fiche, comme un PUT."""
    product_id = sheet.product.id
    _delete_context_rows(session, product_id)
    if sheet.pricing is not None:
        if sheet.pricing.price is not None:
            base, tax, tax_rate = _colonnes_du_prix(sheet.pricing.price)
            session.merge(
                ProductPriceRow(product_id=product_id, base=base, tax=tax, tax_rate=tax_rate)
            )
        session.add_all(
            ProductDiscountRow(product_id=product_id, discount=discount)
            for discount in sheet.pricing.discounts
        )
    if sheet.transport is not None:
        charge = sheet.transport.kilos_volume
        session.merge(
            ProductTransportRow(
                product_id=product_id,
                kilos=charge.kilos if charge else None,
                volume=charge.volume if charge else None,
            )
        )
    if sheet.stock is not None:
        session.merge(
            ProductStockRow(
                product_id=product_id,
                quantity=sheet.stock.quantity,
                stock=sheet.stock.stock,
                warehouse_location=(
                    sheet.stock.warehouse.location if sheet.stock.warehouse else None
                ),
            )
        )
    if sheet.supply is not None:
        session.merge(ProductSupplyRow(product_id=product_id, supplier_id=sheet.supply.supplier_id))
        session.add_all(
            ProductSupplierRegionRow(
                product_id=product_id,
                region=line.region,
                name=line.supplier.name,
                siren=line.supplier.siren_tva.siren if line.supplier.siren_tva else None,
                tva_id=line.supplier.siren_tva.tva_id if line.supplier.siren_tva else None,
            )
            for line in sheet.supply.regions
        )


def _delete_context_rows(session: Session, product_id: ProductId) -> None:
    for model in (
        ProductPriceRow,
        ProductDiscountRow,
        ProductTransportRow,
        ProductStockRow,
        ProductSupplyRow,
        ProductSupplierRegionRow,
    ):
        session.execute(delete(model).where(model.product_id == product_id))
