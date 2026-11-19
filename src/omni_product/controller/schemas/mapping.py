from omni_product.anemic_model import (
    NonExpiringProduct,
    PerishableProduct,
    Price,
    Product,
    ProductPricing,
    ProductStorage,
    ProductSupply,
    ProductTransport,
    RegionSupplier,
    Supplier,
    Warehouse,
)
from omni_product.controller.schemas.product import (
    PriceSchema,
    ProductKind,
    ProductSchema,
    RegionSupplierSchema,
    WarehouseSchema,
)
from omni_product.controller.schemas.supplier import SupplierSchema
from omni_product.dal.product_dal import ProductContext


def _kind_of(product: Product) -> ProductKind:
    if isinstance(product, PerishableProduct):
        return "perishable"
    if isinstance(product, NonExpiringProduct):
        return "non_expiring"
    return "standard"


def product_to_schema(
    product: Product,
    pricing: ProductPricing,
    storage: ProductStorage,
    transport: ProductTransport,
    supply: ProductSupply,
) -> ProductSchema:
    """La réponse HTTP est le seul endroit où les contextes du produit se rejoignent."""
    perishable = product if isinstance(product, PerishableProduct) else None
    return ProductSchema(
        id=product.id,
        kind=_kind_of(product),
        name=product.name,
        slug=product.slug,
        expiration_date=perishable.expiration_date if perishable else None,
        shelf_life_days=perishable.shelf_life_days if perishable else None,
        price=PriceSchema.model_validate(pricing.price) if pricing.price else None,
        discounts=list(pricing.discounts),
        images=dict(product.images),
        suppliers_regions={
            region: RegionSupplierSchema.model_validate(supplier)
            for region, supplier in supply.suppliers_regions.items()
        },
        kilos=transport.kilos,
        volume=transport.volume,
        quantity=storage.quantity,
        stock=storage.stock,
        warehouse=WarehouseSchema.model_validate(storage.warehouse) if storage.warehouse else None,
        supplier_id=supply.supplier_id,
    )


def schema_to_product(schema: ProductSchema, product_id: str) -> Product:
    """Construit une entité neuve ; l'enregistrement la fusionne avec l'existante (`PUT`)."""
    return _product_of(schema, product_id)


def schema_to_contexts(schema: ProductSchema, product_id: str) -> list[ProductContext]:
    """Ce que chaque contexte retient du corps de la requête, relié au produit par son id."""
    return [
        _pricing_of(schema, product_id),
        _storage_of(schema, product_id),
        ProductTransport(product_id=product_id, kilos=schema.kilos, volume=schema.volume),
        ProductSupply(
            product_id=product_id,
            supplier_id=schema.supplier_id,
            suppliers_regions={
                region: RegionSupplier(**supplier.model_dump())
                for region, supplier in (schema.suppliers_regions or {}).items()
            },
        ),
    ]


def _product_of(schema: ProductSchema, product_id: str) -> Product:
    match schema.kind:
        case "perishable":
            product = PerishableProduct(
                id=product_id,
                name=schema.name,
                slug=schema.slug,
                expiration_date=schema.expiration_date,
                shelf_life_days=schema.shelf_life_days,
            )
        case "non_expiring":
            product = NonExpiringProduct(id=product_id, name=schema.name, slug=schema.slug)
        case _:
            product = Product(id=product_id, name=schema.name, slug=schema.slug)
    product.images = schema.images or {}
    return product


def _pricing_of(schema: ProductSchema, product_id: str) -> ProductPricing:
    pricing = ProductPricing(product_id=product_id, discounts=schema.discounts or [])
    if schema.price is not None:
        pricing.price = Price(**schema.price.model_dump())
    return pricing


def _storage_of(schema: ProductSchema, product_id: str) -> ProductStorage:
    storage = ProductStorage(
        product_id=product_id,
        quantity=schema.quantity if schema.quantity is not None else schema.stock,
        stock=schema.stock or 0,
    )
    if schema.warehouse is not None:
        storage.warehouse = Warehouse(**schema.warehouse.model_dump())
    return storage


def supplier_to_schema(supplier: Supplier) -> SupplierSchema:
    return SupplierSchema.model_validate(supplier)
