from datetime import date
from typing import Any

from result import Err, Ok, Result

from omni_product.controller.schemas.product import (
    PriceSchema,
    ProductKind,
    ProductSchema,
    RegionSupplierSchema,
    WarehouseSchema,
)
from omni_product.controller.schemas.supplier import SupplierSchema
from omni_product.dal.product_dal import ProductSheet
from omni_product.dal.records import optional, raw
from omni_product.domain.model import (
    Amount,
    Discount,
    ImageDetail,
    ImageKey,
    Kilos,
    Location,
    NonExpiring,
    ParDateEtDuree,
    ParDateLimite,
    ParDureeDeConservation,
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
    Region,
    ShelfLife,
    ShelfLifeDays,
    Siren,
    Slug,
    Stock,
    Supplier,
    SupplierByRegion,
    SupplierId,
    TvaId,
    Volume,
    Warehouse,
    charge_of,
    perissable_of,
    prix_of,
    region_supplier_of,
)
from omni_product.domain.model.errors import ErreurProduit, InvalidValueError
from omni_product.domain.model.invariants import optionnel, premiere_erreur


def _kind_of(product: Product) -> ProductKind:
    match product.shelf_life:
        case ParDateLimite() | ParDureeDeConservation() | ParDateEtDuree():
            return "perishable"
        case NonExpiring():
            return "non_expiring"
        case None:
            return "standard"


def _durees_de(shelf_life: ShelfLife | None) -> tuple[date | None, int | None]:
    """La date limite et la durée de conservation d'un produit, à plat dans l'API."""
    match shelf_life:
        case ParDateLimite(expiration_date=date_limite):
            return date_limite, None
        case ParDureeDeConservation(shelf_life_days=duree):
            return None, duree.value
        case ParDateEtDuree(expiration_date=date_limite, shelf_life_days=duree):
            return date_limite, duree.value
        case _:
            return None, None


def _price_schema(price: Price | None) -> PriceSchema | None:
    match price:
        case None:
            return None
        case PrixHorsTaxe(base=base):
            return PriceSchema(base=raw(base))
        case PrixAvecTaxe(base=base, tax=tax, tax_rate=tax_rate):
            return PriceSchema(base=raw(base), tax=raw(tax), tax_rate=raw(tax_rate))


def product_to_schema(sheet: ProductSheet) -> ProductSchema:
    product = sheet.product
    expiration_date, shelf_life_days = _durees_de(product.shelf_life)
    pricing = sheet.pricing
    transport = sheet.transport
    stock = sheet.stock
    supply = sheet.supply
    charge = transport.kilos_volume if transport is not None else None
    return ProductSchema(
        id=product.id.value,
        kind=_kind_of(product),
        name=product.name,
        slug=product.slug.value,
        expiration_date=expiration_date,
        shelf_life_days=shelf_life_days,
        price=_price_schema(pricing.price if pricing is not None else None),
        discounts=[discount.value for discount in pricing.discounts] if pricing else [],
        images={image.key.value: raw(image.detail) for image in product.images},
        suppliers_regions=(
            {
                line.region.value: RegionSupplierSchema(
                    name=line.supplier.name,
                    siren=raw(line.supplier.siren_tva.siren) if line.supplier.siren_tva else None,
                    tva_id=raw(line.supplier.siren_tva.tva_id) if line.supplier.siren_tva else None,
                )
                for line in supply.regions
            }
            if supply is not None
            else {}
        ),
        kilos=raw(charge.kilos) if charge is not None else None,
        volume=raw(charge.volume) if charge is not None else None,
        quantity=raw(stock.quantity) if stock is not None else None,
        stock=raw(stock.stock) if stock is not None else None,
        warehouse=(
            WarehouseSchema(location=raw(stock.warehouse.location))
            if stock is not None and stock.warehouse is not None
            else None
        ),
        supplier_id=raw(supply.supplier_id) if supply is not None else None,
    )


def schema_to_product(
    schema: ProductSchema, product_id: str
) -> Result[ProductSheet, InvalidValueError]:
    """Construit une fiche neuve ; `save` la fusionne avec l'existante (comme `PUT` en Java).

    Chaque valeur est d'abord validée avec `of()`. Les fabriques des variantes (périssable, prix,
    charge, fournisseurs) rendent ensuite un résultat : le premier échec remonte à l'appelant.
    """
    # Un produit doit avoir un nom et un slug : sans eux, la base refusait l'écriture.
    if schema.name is None:
        return Err(ErreurProduit("Product name is missing"))
    if schema.slug is None:
        return Err(ErreurProduit("Product slug is missing"))
    erreur = premiere_erreur(_valeurs_a_valider(schema, product_id, schema.slug))
    if erreur is not None:
        return Err(erreur)
    price = schema.price
    shelf_life = _shelf_life_of(schema)
    prix = prix_of(
        price.base if price is not None else None,
        price.tax if price is not None else None,
        price.tax_rate if price is not None else None,
    )
    charge = charge_of(schema.kilos, schema.volume)
    fournisseurs = _fournisseurs_of(schema)
    erreur = premiere_erreur([shelf_life, prix, charge, fournisseurs])
    if erreur is not None:
        return Err(erreur)
    name = schema.name
    slug = Slug(schema.slug)
    pid = ProductId(product_id)
    images = tuple(
        ProductImage(key=ImageKey(key), detail=optional(ImageDetail, detail))
        for key, detail in (schema.images or {}).items()
    )
    product = Product(id=pid, name=name, slug=slug, images=images, shelf_life=shelf_life.unwrap())
    warehouse = schema.warehouse
    quantite = schema.quantity if schema.quantity is not None else (schema.stock or 0)
    return Ok(
        ProductSheet(
            product=product,
            pricing=ProductPrice(
                id=pid,
                price=prix.unwrap(),
                discounts=tuple(Discount(value) for value in schema.discounts or []),
            ),
            transport=ProductTransport(id=pid, kilos_volume=charge.unwrap()),
            stock=ProductStock(
                id=pid,
                quantity=Quantity(quantite),
                stock=Stock(schema.stock or 0),
                warehouse=(
                    Warehouse(location=optional(Location, warehouse.location))
                    if warehouse
                    else None
                ),
            ),
            supply=ProductSupply(
                id=pid,
                supplier_id=optional(SupplierId, schema.supplier_id),
                regions=fournisseurs.unwrap(),
            ),
        )
    )


def _shelf_life_of(schema: ProductSchema) -> Result[ShelfLife | None, InvalidValueError]:
    match schema.kind:
        case "perishable":
            return perissable_of(schema.expiration_date, schema.shelf_life_days)
        case "non_expiring":
            return Ok(NonExpiring())
        case _:
            return Ok(None)


def _fournisseurs_of(
    schema: ProductSchema,
) -> Result[tuple[SupplierByRegion, ...], InvalidValueError]:
    lignes: list[SupplierByRegion] = []
    for region, supplier in (schema.suppliers_regions or {}).items():
        match region_supplier_of(supplier.name, supplier.siren, supplier.tva_id):
            case Err(erreur):
                return Err(erreur)
            case Ok(fournisseur):
                lignes.append(SupplierByRegion(region=Region(region), supplier=fournisseur))
    return Ok(tuple(lignes))


def _valeurs_a_valider(
    schema: ProductSchema, product_id: str, slug: str
) -> list[Result[Any, InvalidValueError]]:
    """Toutes les valeurs de la fiche qui passent par une fabrique `of()`."""
    images = schema.images or {}
    quantite = schema.quantity if schema.quantity is not None else (schema.stock or 0)
    return [
        ProductId.of(product_id),
        Slug.of(slug),
        *(ImageKey.of(key) for key in images),
        *(optionnel(ImageDetail.of, detail) for detail in images.values()),
        *(
            [optionnel(ShelfLifeDays.of, schema.shelf_life_days)]
            if schema.kind == "perishable"
            else []
        ),
        *(Discount.of(value) for value in schema.discounts or []),
        *_valeurs_du_prix(schema.price),
        optionnel(Kilos.of, schema.kilos),
        optionnel(Volume.of, schema.volume),
        Quantity.of(quantite),
        Stock.of(schema.stock or 0),
        *_valeurs_de_l_entrepot(schema.warehouse),
        optionnel(SupplierId.of, schema.supplier_id),
        *_valeurs_des_fournisseurs(schema.suppliers_regions or {}),
    ]


def _valeurs_du_prix(price: PriceSchema | None) -> list[Result[Any, InvalidValueError]]:
    if price is None:
        return []
    return [
        optionnel(Amount.of, price.base),
        optionnel(Amount.of, price.tax),
        optionnel(Rate.of, price.tax_rate),
    ]


def _valeurs_de_l_entrepot(
    warehouse: WarehouseSchema | None,
) -> list[Result[Any, InvalidValueError]]:
    if warehouse is None:
        return []
    return [optionnel(Location.of, warehouse.location)]


def _valeurs_des_fournisseurs(
    regions: dict[str, RegionSupplierSchema],
) -> list[Result[Any, InvalidValueError]]:
    return [
        valeur
        for region, supplier in regions.items()
        for valeur in (
            Region.of(region),
            optionnel(Siren.of, supplier.siren),
            optionnel(TvaId.of, supplier.tva_id),
        )
    ]


def supplier_to_schema(supplier: Supplier) -> SupplierSchema:
    return SupplierSchema(id=supplier.id.value, name=supplier.name)
